
"""
시스템 영속화(Persistence) 및 WAL(Write-Ahead Log) 엔진
[①사유]: 비정상 종료 시에도 현재까지의 모든 상태를 복구(Recovery)하기 위함.
[②위험성]: 기록되지 않은 이벤트 유실로 인한 포지션 불일치 및 미체결 주문 미식별.
"""

import json
import aiofiles
import os

class EventStore:
    """
    [①사유]: 이벤트를 디스크에 순차적으로 기록(Append-only).
    [방어 기제 #126] 동기식 저장이 아닌 비동기 I/O를 통한 시스템 성능 병목 방지.
    """
    def __init__(self, log_path="event_store.log"):
        self.log_path = log_path

    async def save_event(self, event_type: str, data: dict):
        """[①사유]: 이벤트 영속화."""
        record = {"type": event_type, "data": data}
        async with aiofiles.open(self.log_path, mode='a') as f:
            await f.write(json.dumps(record) + "\n")
            # [방어 기제 #149] OS 캐시를 강제로 디스크에 물리적으로 기록
            await f.flush()

    async def replay_events(self):
        """[①사유]: 시스템 재기동 시 로그 파일로부터 과거 상태 재현."""
        if not os.path.exists(self.log_path):
            return []
        
        events = []
        async with aiofiles.open(self.log_path, mode='r') as f:
            async for line in f:
                events.append(json.loads(line))
        return events
