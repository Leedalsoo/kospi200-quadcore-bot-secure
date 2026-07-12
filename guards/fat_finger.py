"""
[①사유]: Fat-Finger(오입력) 주문 원천 차단 및 리스크 방지.
[②방어 기제 #36, #165]: 가격 이탈 및 수량 폭주 방지 2중 검증.
"""

import logging

class FatFingerGuard:
    def __init__(self, max_deviation: float = 0.05, max_qty: int = 100):
        # [세부 운영 수치]
        # max_deviation: 5% 이상 가격 이탈 시 차단
        # max_qty: 1회 주문 최대 100계약 제한
        self.max_deviation = max_deviation
        self.max_qty = max_qty
        self.logger = logging.getLogger("FatFingerGuard")

    def is_safe(self, order_price: float, current_market_price: float, qty: int) -> bool:
        """[①사유]: 주문 요청 데이터의 무결성 및 리스크 범위 검증."""
        
        # 1. 수량 검증
        if qty <= 0 or qty > self.max_qty:
            self.logger.error(f"Qty Limit Exceeded: {qty} (Max: {self.max_qty})")
            return False
            
        # 2. 가격 검증 (0으로 나누기 방어 로직 포함)
        if current_market_price <= 0:
            self.logger.warning("Market price is zero or invalid, blocking order.")
            return False
            
        price_deviation = abs(order_price - current_market_price) / current_market_price
        
        # 3. 편차 검증 및 상세 로그
        if price_deviation > self.max_deviation:
            self.logger.error(
                f"Price Deviation Blocked! Price: {order_price}, "
                f"Market: {current_market_price}, Deviation: {price_deviation:.2%}"
            )
            return False
            
        return True
