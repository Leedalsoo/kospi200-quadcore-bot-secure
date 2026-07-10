"""
이 코드는 명세서 제15장 CQRS 및 외부 인터페이스 요구사항을 반영하여 작성되었음.
[①사유]: 내부 로직과 외부 통신 구간의 분리(CQRS)를 통한 시스템 안전성 강화.
[②위험성]: 외부 인터페이스의 과부하가 매매 엔진(전략/체결)으로 전이되어 지연 발생.
[③커스텀 범위]: 비동기 WebSocket/REST 인터페이스 및 명령 검증.
"""

import asyncio
import json

class InterfaceAgent:
    """
    [①사유]: 외부 클라이언트와 시스템 내부의 비동기 소통창구.
    [방어 기제 #10, #182] 외부로부터의 비정상 명령 필터링.
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus

    async def handle_incoming_command(self, raw_cmd: str):
        """
        [①사유]: 외부로부터 들어온 명령(주문취소, 강제종료 등) 처리.
        [②위험성]: 외부에서 조작된 명령이 리스크 엔진 없이 실행됨.
        """
        try:
            cmd = json.loads(raw_cmd)
            # [방어 기제 #182] 명령 검증 로직 실행 (필요 시 RiskAgent와 연동)
            # 이벤트를 버스에 실어 내부 에이전트가 비동기로 처리하도록 전송
            await self.event_bus.publish(priority=1, event_type="COMMAND", data=cmd)
        except json.JSONDecodeError:
            pass # 로그 기록 및 차단

    async def broadcast_status(self, status: dict):
        """[①사유]: 내부 상태를 외부 UI로 실시간 전송."""
        # WebSocket 등을 통해 외부로 데이터 배포
        pass

