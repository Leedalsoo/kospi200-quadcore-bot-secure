"""
이 코드는 명세서 제6장 및 이벤트소싱 요구사항을 반영하여 작성되었음.
[①사유]: 모든 모듈 간 결합도 제거(Decoupling) 및 비동기 메시지 전달.
[②위험성]: 이벤트 처리 지연 시 전체 시스템 스톨(Stall) 발생.
[③커스텀 범위]: asyncio.PriorityQueue 기반 우선순위 이벤트 처리.
"""

import asyncio
from typing import Any, Callable, Dict, List

class EventBus:
    """
    [①사유]: 고속 이벤트 라우팅 및 우선순위 제어.
    [방어 기제 #5, #71] 우선순위 기반 이벤트 스케줄링.
    """
    def __init__(self):
        # [방어 기제 #89] 우선순위 큐 (낮은 숫자가 높은 우선순위)
        self.queue = asyncio.PriorityQueue()
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """[①사유]: 특정 이벤트 구독 등록."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def publish(self, priority: int, event_type: str, data: Any):
        """
        [①사유]: 이벤트 발행. 
        [②위험성]: 큐 가득 찰 경우 이벤트 유실.
        """
        await self.queue.put((priority, event_type, data))

    async def start_loop(self):
        """[①사유]: 이벤트 루프 가동 및 라우팅."""
        while True:
            priority, event_type, data = await self.queue.get()
            if event_type in self.subscribers:
                for callback in self.subscribers[event_type]:
                    await callback(data)
            self.queue.task_done()

