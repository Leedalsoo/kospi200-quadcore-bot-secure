"""
시스템 외부 통신 및 제어 인터페이스 (CQRS)
[①사유]: 외부 클라이언트(UI, API)와 내부 매매 엔진 간의 물리적/논리적 결합 차단.
[②위험성]: 외부 인터페이스의 과부하 및 보안 취약점이 매매 전략/체결 에이전트로 전이.
"""

import json
import asyncio
import logging

class InterfaceAgent:
    """
    [①사유]: 외부와 소통하는 유일한 창구.
    [방어 기제 #10, #182] 외부의 비정상적 명령은 '명령(Command)'만 발행하고,
    시스템의 모든 정보는 '조회(Query)'로만 내보내어 격리.
    """
    def __init__(self, event_bus):
        self.bus = event_bus
        self.logger = logging.getLogger("InterfaceAgent")

    async def handle_external_command(self, raw_data: str):
        """
        [①사유]: 외부 명령을 시스템 내부의 이벤트로 변환.
        [방어 기제 #182] 명령 검증 및 우선순위 할당.
        """
        try:
            cmd = json.loads(raw_data)
            # 시스템 내부로 전달되는 명령은 오직 이벤트 버스를 통해서만 이동
            await self.bus.publish(priority=0, event_type="EXTERNAL_COMMAND", data=cmd)
            self.logger.info(f"Command received and queued: {cmd.get('type')}")
        except json.JSONDecodeError:
            self.logger.error("Invalid command format received.")

    async def push_status_update(self, status: dict):
        """
        [①사유]: 내부 상태 정보(포지션, 체결가 등)를 외부로 브로드캐스트.
        [방어 기제 #15] 조회 로직과 명령 로직의 분리 (CQRS).
        """
        # 외부 클라이언트(웹소켓 등)로 데이터 전송
        # 내부 로직에 영향을 주지 않도록 별도 태스크로 처리
        pass
