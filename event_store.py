"""
이 코드는 마스터 SDD 3.0의 [제 13장: 영속성 및 이벤트 소싱] 요구사항을 반영하여 작성되었음 [참조: #349, #350].
모든 상태 변경 이력을 순차적으로 물리 디스크에 기록하는 WAL(Write-Ahead Logging) 엔진.
"""

import json
import os
from datetime import datetime
from typing import Any

class EventStore:
    def __init__(self, log_path: str = "logs/system_events.jsonl"):
        self.log_path = log_path
        # [방어 기제 #75] 데이터 저장 경로 분리
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    async def save_event(self, event_type: str, data: Any):
        """
        [방어 기제 #36, #90] WAL 선행 기록 및 물리적 동기화(fsync).
        """
        event_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        # [방어 기제 #40, #118] 원자적 기록 및 파편화 방지
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_entry) + "\n")
            f.flush()
            os.fsync(f.fileno()) # [방어 기제 #90] 물리적 동기화 강제

    async def load_history(self):
        """
        [방어 기제 #16] 재기동 시 상태 복구를 위한 이벤트 로드.
        """
        if not os.path.exists(self.log_path):
            return []
            
        history = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                history.append(json.loads(line))
        return history # 수정됨: 'events'를 'history'로 정확히 반환
        """
        if not os.path.exists(self.log_path):
            return []
            
        history = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                history.append(json.loads(line))
        return history
        return events
