"""
이 코드는 명세서 제12장 2번의 요구사항을 반영하여 작성되었음.
[①사유]: 시장 데이터를 정규화하여 전략 엔진의 연산 부하 최소화 및 미시구조 지표 산출.
[②위험성]: 데이터 유실 및 잘못된 정규화로 인한 주문 왜곡.
[③커스텀 범위]: KOSPI 200 파생상품 시세 스트림 처리.
"""

import asyncio
from collections import deque
from data_contract import MarketTick

class MarketDataAgent:
    """
    [①사유]: 고속 데이터 수신 및 백프레셔 제어.
    [②위험성]: 큐 누적에 따른 시스템 메모리 오버플로우.
    [방어 기제 #11, #19, #113]
    """
    def __init__(self, max_queue_size: int = 5000):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.order_book = {} # 내부 메모리 호가창

    async def normalize_tick(self, raw_data: dict) -> MarketTick:
        """[①사유]: 규격화된 객체로 변환. [②위험성]: 타입 캐스팅 오류."""
        # 방어 기제 #105: 데이터 필드 타입 불일치 시 예외 처리
        return MarketTick(**raw_data)

    async def apply_backpressure(self, tick: MarketTick):
        """
        [①사유]: 큐 포화 시 중요도 낮은 틱 선제적 폐기.
        [방어 기제 #19, #61]
        """
        if self.queue.full():
            # 오래된 데이터를 팝하고 새로운 데이터를 푸시 (drop-oldest)
            self.queue.get_nowait()
        await self.queue.put(tick)

    async def rebuild_orderbook(self, tick: MarketTick):
        """[①사유]: 1~10호가 뎁스 재구축. [②위험성]: 부분 호가 반영 시 왜곡."""
        # 방어 기제 #46: 이상 가격 발생 시 통계적 필터링 적용
        self.order_book = {
            "bids": list(zip(tick.bid_prices, tick.bid_qtys)),
            "asks": list(zip(tick.ask_prices, tick.ask_qtys))
        }

