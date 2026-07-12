"""
[①사유]: 거래소 틱 데이터 정규화 및 LOB 미시구조 분석.
[방어 기제 #46, #69]: 호가 불균형 및 가격 이상치 실시간 필터링.
"""

import logging
from typing import Dict
from data_contract import MarketTick

class MarketDataAgent:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("MarketDataAgent")
        
        # [세부 운영 수치]
        self.params = {
            "price_volatility_limit": 0.05,  # 5% 이상 급변동 시 이상치 간주
            "min_liquidity_qty": 10,         # 호가 잔량 부족 경고 기준
            "spread_anomaly_limit": 0.2      # 0.2pt 이상 스프레드 시 비정상 징후
        }
        self.last_price: float = 0.0

    async def on_tick(self, tick: MarketTick):
        """
        [①사유]: 틱 수신 시 LOB 정규화 및 리스크 필터링.
        """
        # 1. 가격 이상치(Outlier) 체크
        if self.last_price != 0 and abs(tick.last_price - self.last_price) / self.last_price > self.params["price_volatility_limit"]:
            self.logger.error(f"Critical Outlier: {tick.last_price}")
            await self.event_bus.publish(priority=0, event_type="CRITICAL_ALERT", data={"msg": "Price Outlier"})
            return

        # 2. 호가 스프레드 이상 징후 탐지
        spread = tick.ask_price - tick.bid_price
        if spread > self.params["spread_anomaly_limit"]:
            self.logger.warning(f"Abnormal Spread: {spread}")

        # 3. LOB 정규화 (데이터 계약 규격화)
        self.order_book = {
            "bids": sorted(zip(tick.bid_prices, tick.bid_qtys), key=lambda x: x[0], reverse=True),
            "asks": sorted(zip(tick.ask_prices, tick.ask_qtys), key=lambda x: x[0]),
            "timestamp": tick.timestamp
        }
        
        self.last_price = tick.last_price
        
        # 4. 정규화된 데이터 및 LOB 상태 전송
        await self.event_bus.publish(priority=3, event_type="NORMALIZED_TICK", data={"tick": tick, "lob": self.order_book})
        self.logger.info(f"Market Data Processed: Price {self.last_price}")
