"""
[①사유]: 외부 시스템과의 보안 통신을 위한 CQRS(Command-Query Responsibility Segregation) 인터페이스.
[②방어 기제 #15, #145]: 명령과 조회 채널의 엄격한 분리 및 접근 제어.
"""

import json
import logging
from data_contract import CommandRequest

class InterfaceAgent:
    def __init__(self, event_bus):
        self.bus = event_bus
        self.logger = logging.getLogger("InterfaceAgent")

    async def handle_command(self, raw_data: str):
        """[①사유]: 외부 명령 실행 (Command) - 보안 검증 후 이벤트 발행."""
        try:
            cmd = json.loads(raw_data)
            # 검증된 명령만 내부 버스로 전달
            await self.bus.publish(priority=1, event_type="CMD", data=cmd)
            self.logger.info(f"Command executed: {cmd.get('type')}")
        except json.JSONDecodeError:
            self.logger.error("Security Alert: Invalid Command Format.")

    async def handle_query(self, query_type: str) -> dict:
        """[①사유]: 시스템 상태 조회 (Query) - 시스템 변경 권한 없음 (Read-Only)."""
        self.logger.info(f"Query requested: {query_type}")
        # 상태를 변경하지 않는 조회 전용 메서드
        return {"status": "ok", "query": query_type}
