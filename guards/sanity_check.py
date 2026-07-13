"""
[①사유]: 설정 파일 기반의 동적 수치 검증 엔진.
[②방어 기제 #35, #116]: 시장가 범위 이탈 및 비현실적 데이터 차단.
"""

import logging

class SanityCheckGuard:
    def __init__(self, config):
        """
        [①사유]: ConfigAgent 객체를 주입받아 동적 설정 로드.
        [②방어 기제]: 하드코딩된 수치를 제거하고 중앙 집중식 제어 전환.
        """
        # config/hard_limits.yaml의 guardrails 섹션 내 sanity_check 로드
        self.limits = config.get("guardrails")["sanity_check"]
        self.logger = logging.getLogger("SanityCheckGuard")

    def validate(self, price: float, volume: int) -> bool:
        """
        [①사유]: 시장 데이터의 수치적 현실성 동적 검증.
        [방어 기제]: 설정된 범위를 벗어날 경우 차단.
        """
        # 1. 가격 범위 검증 (config 설정값 사용)
        if not (self.limits["min_price"] <= price <= self.limits["max_price"]):
            self.logger.error(f"Price Out of Bounds: {price} (Limit: {self.limits['min_price']}~{self.limits['max_price']}). Blocking Data.")
            return False
            
        # 2. 거래량 비현실성 검증
        if volume < 0:
            self.logger.error(f"Invalid Volume Detected: {volume}.")
            return False
            
        return True
