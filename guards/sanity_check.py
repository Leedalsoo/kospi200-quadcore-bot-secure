"""
[①사유]: 수신 데이터의 현실성 및 건전성 검증.
[②방어 기제 #35, #116]: 시장가 범위 이탈 및 비현실적 데이터 차단.
"""

import logging

class SanityCheckGuard:
    def __init__(self, min_price: float = 1.0, max_price: float = 1000.0):
        # [세부 운영 수치]
        # KOSPI200 옵션 가격 범위를 현실적으로 제한하여, 
        # 비정상적인 데이터(예: 0원 또는 수만 원)를 즉시 배제
        self.min_price = min_price
        self.max_price = max_price
        self.logger = logging.getLogger("SanityCheckGuard")

    def is_sane(self, price: float, volume: int) -> bool:
        """[①사유]: 시장 데이터의 수치적 현실성 검증."""
        
        # 1. 가격 범위 검증
        if not (self.min_price <= price <= self.max_price):
            self.logger.error(f"Price Out of Bounds: {price}. Blocking Data.")
            return False
            
        # 2. 거래량 비현실성 검증
        if volume < 0:
            self.logger.error(f"Invalid Volume Detected: {volume}.")
            return False
            
        return True
