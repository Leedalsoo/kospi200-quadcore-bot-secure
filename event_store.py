"""
이 코드는 명세서 제7장 및 제15장의 요구사항을 반영하여 작성되었음.
[①사유]: 시스템 크래시 시 상태 복구를 위한 이벤트 영속화 및 비동기 I/O 처리.
[②위험성]: 로깅 병목 발생 시 매매 엔진 레이턴시 전이 및 데이터 유실 시 복구 불능.
[③커스텀 범위]: JSONL 기반 비동기 WAL(Write-Ahead Log) 엔진.
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

class TradingJSONEncoder(json.JSONEncoder):
    """
    [①사유]: Decimal, UUID, datetime 등 금융 특화 객체의 JSON 직렬화 지원.
    [②위험성]: 인코딩 실패 시 로그 기록 중단 및 복구 데이터 오염.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class EventStoreAgent:
    """
    [①사유]: 메인 루프를 블로킹하지 않는 고속 이벤트 기록기.
    [②위험성]: 파일 쓰기 지연(Stall) 발생 시 전략 엔진의 틱 처리 지연.
    """
    def __init__(self, log_path: str = "logs/wal.jsonl"):
        self.log_path = log_path
        # [방어 기제 #8, #184] 비동기 순차 기록을 위한 단일 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._ensure_log_dir()
        self.log_file = open(self.log_path, mode="a", encoding="utf-8", buffering=1)
        self.event_count = 0

    def _ensure_log_dir(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def append_event(self, event_type: str, payload: dict):
        """
        [①사유]: 모든 상태 변경 이벤트를 디스크에 기록. 
        [②위험성]: 기록 전 시스템 종료 시 복구 불가(WAL 원칙 준수).
        [방어 기제 #36, #90, #169]
        """
        log_entry = {
            "type": event_type,
            "data": payload,
            "recorded_at": datetime.now().isoformat(),
            "seq": self.event_count
        }
        # 비동기적으로 파일에 기록하여 매매 엔진 레이턴시 보호
        self.executor.submit(self._write_to_disk, log_entry)
        self.event_count += 1
        
        # 1,000번째 이벤트마다 스냅샷 예약 트리거 (구조만 생성)
        if self.event_count % 1000 == 0:
            self.trigger_snapshot()

    def _write_to_disk(self, entry: dict):
        """실제 물리적 쓰기 및 커널 버퍼 동기화(fsync)."""
        line = json.dumps(entry, cls=TradingJSONEncoder)
        self.log_file.write(line + "\n")
        self.log_file.flush() # [방어 기제 #169] 커널 버퍼 강제 동기화
        os.fsync(self.log_file.fileno()) # 물리 디스크 쓰기 보장

    def trigger_snapshot(self):
        """[①사유]: 복구 속도 최적화를 위한 상태 스냅샷. [②위험성]: 스냅샷 시점 오차."""
        # 향후 State Agent와 연동하여 메모리 덤프 로직 구현 예정
        pass 

    def graceful_shutdown(self):
        """
        [①사유]: 종료 시 잔여 로그 완전 비우기. 
        [②위험성]: 큐에 남은 중요 체결 로그 소실 방지.
        [방어 기제 #117, #190]
        """
        self.executor.shutdown(wait=True)
        if self.log_file:
            self.log_file.close()

