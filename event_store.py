"""
[①사유]: WAL 엔진의 안정성 고도화 및 데이터 무결성 보장.
[②방어 기제 #75, #90, #118]: 로그 로테이션 및 물리적 동기화 최적화.
"""

import json
import os
import hashlib
import logging  # 에러 해결을 위해 추가
from datetime import datetime
from typing import Any, List

class EventStore:
    def __init__(self, log_path: str = "logs/system_events.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        
        # [세부 운영 수치]
        self.params = {
            "max_file_size": 100 * 1024 * 1024,  # 100MB 도달 시 로그 회전
            "buffer_threshold": 10              # 10개 이벤트마다 강제 동기화
        }
        self.event_count = 0
        self.logger = logging.getLogger("EventStore")

    def _generate_checksum(self, data: str) -> str:
        """[방어 기제 #120]: 데이터 변조 탐지 체크섬."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    async def save_event(self, event_type: str, data: Any):
        """[①사유]: WAL 선행 기록 및 물리적 동기화."""
        event_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        json_data = json.dumps(event_entry)
        entry_with_checksum = f"{json_data}|{self._generate_checksum(json_data)}\n"

        if os.path.exists(self.log_path) and os.path.getsize(self.log_path) > self.params["max_file_size"]:
            os.rename(self.log_path, f"{self.log_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}")

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry_with_checksum)
            self.event_count += 1
            
            if self.event_count >= self.params["buffer_threshold"]:
                f.flush()
                os.fsync(f.fileno())
                self.event_count = 0

    async def load_history(self) -> List[dict]:
        """[①사유]: 무결성 검증을 포함한 로그 복구."""
        if not os.path.exists(self.log_path):
            return []
            
        history = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    parts = line.strip().split('|')
                    if len(parts) != 2:
                        continue
                    data, checksum = parts
                    if self._generate_checksum(data) == checksum:
                        history.append(json.loads(data))
                    else:
                        self.logger.error("Corrupted event log detected!")
                except Exception as e:
                    self.logger.error(f"Failed to load event: {e}")
        return history
