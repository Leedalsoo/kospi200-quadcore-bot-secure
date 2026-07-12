"""
[①사유]: 마진 다이어트 및 MDD(Maximum Drawdown) 셧다운 로직.
[②방어 기제 #50, #153, #212]: 과도한 손실 방지 및 자동 셧다운 트리거.
"""

import logging

class MarginDietGuard:
    def __init__(self, mdd_threshold: float = 0.10, min_margin_ratio: float = 0.50):
        # [세부 운영 수치]
        # mdd_threshold: 계좌 잔고 대비 10% 손실 시 시스템 셧다운
        # min_margin_ratio: 증거금 유지 비율 50% 미만 시 신규 진입 차단
        self.mdd_threshold = mdd_threshold
        self.min_margin_ratio = min_margin_ratio
        self.logger = logging.getLogger("MarginDietGuard")

    def validate_risk(self, current_balance: float, peak_balance: float, current_margin_ratio: float) -> bool:
        """[①사유]: 실시간 리스크 평가 및 위험 신호 발행."""
        
        # 1. MDD 체크 (최고점 대비 하락률)
        if peak_balance > 0:
            drawdown = (peak_balance - current_balance) / peak_balance
            if drawdown > self.mdd_threshold:
                self.logger.critical(f"MDD Threshold Exceeded! Drawdown: {drawdown:.2%}. Shutting down.")
                return False  # 시스템 즉시 셧다운 신호
        
        # 2. 증거금 유지 비율 체크
        if current_margin_ratio < self.min_margin_ratio:
            self.logger.warning(f"Margin Low: {current_margin_ratio:.2%}. Blocking new orders.")
            return False
            
        return True
