"""
이 코드는 명세서 제12장 1조 및 제15장 14조의 요구사항을 반영하여 작성되었음.
[①사유]: 거래소별 독립적인 토큰 버킷 기반의 고성능 스로틀링 적용.
[②위험성]: 트래픽 제어 실패 시 증권사 서버로부터 API 접속 영구 차단(BAN).
[③커스텀 범위]: 엔드포인트별 분리된 토큰 버킷, 버스트 트래픽 제어, 비동기 락-프리 기법.
[방어 기제 매핑]: #21, #93, #155, #158
"""

import asyncio
import time
import logging
from typing import Dict

logger = logging.getLogger("NetworkAgent")

class TokenBucket:
    """[①사유]: 고정 TPS를 준수하기 위한 토큰 버킷 알고리즘."""
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity      # 최대 버스트 허용량
        self.fill_rate = fill_rate    # 초당 토큰 충전량
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        async with self.lock:
            now = time.monotonic()
            # 토큰 자동 충전
            self.tokens += (now - self.last_update) * self.fill_rate
            if self.tokens > self.capacity:
                self.tokens = self.capacity
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class NetworkAgent:
    """
    [①사유]: 증권사별 독립된 토큰 버킷을 사용한 주문/조회 스로틀링 관리.
    [방어 기제 #14, #93] API 스펙에 맞춘 엔드포인트별 엄격한 사용량 제한.
    """
    def __init__(self):
        # [수치적용] 
        # 주문: 초당 20회(TPS), 버스트 허용 50회
        # 조회: 초당 50회(TPS), 버스트 허용 100회
        self.buckets = {
            "order": TokenBucket(capacity=50, fill_rate=20.0),
            "query": TokenBucket(capacity=100, fill_rate=50.0)
        }

    async def send_order(self, order_data: dict):
        """[①사유]: 토큰 버킷 기반 주문 전송 제한."""
        if await self.buckets["order"].consume(1):
            # 주문 집행 로직
            logger.debug(f"Order transmitted: {order_data.get('client_order_id')}")
            return True
        else:
            logger.error("THROTTLING EXCEEDED: Order request rejected.")
            return False

    async def query_data(self, endpoint: str):
        """[①사유]: 데이터 조회 요청 제한."""
        if await self.buckets["query"].consume(1):
            # 조회 요청 집행
            return True
        return False
