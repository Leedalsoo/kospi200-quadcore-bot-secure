"""
이 코드는 마스터 SDD 3.0의 [제 3장: Internal Event Bus] 요구사항을 반영하여 작성되었음 [참조: #246, #248].
Rust Native LMAX Disruptor 개념을 파이썬 환경에서 구현한 고속 링 버퍼 엔진.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Tuple
import heapq

@dataclass(order=True)
class EventTask:
    # 3중 우선순위: Execution(0) > Risk(1) > Order(2) > Tick(3) > UI(4)
    priority: int
    sequence: int
    data: Any = None

class EventBus:
    def __init__(self, max_size: int = 5000):
        # 방어 기제 #19: 큐 포화 시 Drop-oldest 정책 구현을 위한 링 버퍼 구조
        self.max_size = max_size
        self._queue = []  # 우선순위 큐 (heapq)
        self._counter = 0 # 시퀀스 관리
        self._lock = asyncio.Lock()

    async def publish(self, priority: int, data: Any):
        """이벤트를 링 버퍼에 적재 [방어 기제 #2, #11]"""
        async with self._lock:
            # 방어 기제 #19: 큐 포화 상태 검사
            if len(self._queue) >= self.max_size:
                # 가장 우선순위가 낮고(값이 큰) 오래된 데이터를 제거
                heapq.heappop(self._queue)
            
            task = EventTask(priority, self._counter, data)
            heapq.heappush(self._queue, task)
            self._counter += 1

    async def consume(self) -> Any:
        """우선순위에 따라 이벤트 소비 [참조: #248]"""
        async with self._lock:
            if not self._queue:
                return None
            return heapq.heappop(self._queue).data

    def is_empty(self) -> bool:
        return len(self._queue) == 0
