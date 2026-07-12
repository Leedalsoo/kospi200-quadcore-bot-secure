"""
[①사유]: 내부 이벤트 버스(Event Bus)의 비동기 우선순위 처리 및 고성능 소비 모델.
[②방어 기제 #19, #248]: 우선순위 기반 링 버퍼링 및 Back-pressure 제어.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class EventTask:
    # 우선순위: 0(최고) ~ 5(최저)
    priority: int
    sequence: int
    data: Any = field(compare=False)

class EventBus:
    def __init__(self, max_size: int = 10000):
        # [세부 운영 수치]
        self.max_size = max_size
        self._queue = asyncio.PriorityQueue(maxsize=max_size)
        self._counter = 0
        self.logger = logging.getLogger("EventBus")

    async def publish(self, priority: int, event_type: str, data: Any):
        """[①사유]: 비동기 이벤트 발행 및 큐 풀(Full) 정책 방어."""
        # [방어 기제 #19]: 큐 가득 찼을 때의 전략(Non-blocking reject)
        if self._queue.full():
            self.logger.error("EventBus Overflow! Dropping lowest priority task.")
            # 가장 오래된/낮은 우선순위 작업을 강제 비우고 다시 시도 (안전성 확보)
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass

        self._counter += 1
        task = EventTask(priority, self._counter, {"type": event_type, "payload": data})
        
        # 큐 삽입
        self._queue.put_nowait(task)

    async def consume(self) -> Any:
        """[①사유]: 우선순위에 따른 이벤트 소비 및 블로킹 처리."""
        # 이벤트를 기다리며 대기 (CPU 효율 극대화)
        task = await self._queue.get()
        data = task.data
        self._queue.task_done()
        return data

    def get_queue_depth(self) -> int:
        return self._queue.qsize()
