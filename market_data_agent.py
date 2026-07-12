"""
이 코드는 마스터 SDD 3.0의 [제 7장: 시장 데이터 처리 에이전트] 요구사항을 반영함.
[방어 기제 #46] 비정상 시장가 필터링 및 [방어 기제 #69] LOB 정규화 로직 포함.
"""

import logging
from typing import Dict
# data_contract 모듈에서 MarketTick을 불러와야 에러가 해결됩니다.
from data_contract import MarketTick

class MarketDataAgent:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("MarketDataAgent")
        self.last_price: float = 0.0

    async def on_tick(self, tick: MarketTick):
        """
        [①사유]: 거래소 데이터 수신 및 유효성 검증.
        [방어 기제 #46] 극단적인 가격 변동(Outlier) 차단.
        """
        price = tick.last_price
        
        # 변동성 체크
        if self.last_price != 0 and abs(price - self.last_price) / self.last_price > 0.1:
            self.logger.warning(f"Abnormal Price Detected: {price}. Filtered.")
            await self.event_bus.publish(priority=0, event_type="CRITICAL_ALERT", data={"msg": "Outlier Price"})
            return

        self.last_price = price
        
        # 정규화된 틱 데이터 전송
        await self.event_bus.publish(priority=3, event_type="NORMALIZED_TICK", data=tick)
        self.logger.info(f"Tick Processed: {price}")
        self.order_book = {
            "bids": list(zip(tick.bid_prices, tick.bid_qtys)),
            "asks": list(zip(tick.ask_prices, tick.ask_qtys))
        }

