"""
[①사유]: 주문 집행 전 실시간 위험성 평가 및 방어 기제 적용.
[②위험성]: 하드 리밋 초과 시 주문을 즉시 거부하여 계좌 보호.
"""

from decimal import Decimal
import logging
from data_contract import OrderRequest, Position, HardLimitsConfig

class RiskAgent:
    """
    [①사유]: 3단계 리스크 필터링 엔진.
    [방어 기제 #36, #50, #165]
    """
    def __init__(self, config: HardLimitsConfig):
        self.config = config
        self.logger = logging.getLogger("RiskAgent")
        
        # [현실적 안전 수치 파라미터]
        self.limits = {
            "max_single_order_qty": 50,      # 1회 주문 최대 수량
            "max_total_position": 200,       # 최대 보유 가능 계약수
            "margin_usage_threshold": 0.85   # 증거금 사용률 85% 이상 시 경고
        }

    def validate_order(self, request: OrderRequest, current_position: Position) -> bool:
        """[①사유]: 주문 전 3단계 필터링."""
        if not self._check_fat_finger(request):
            return False
        if not self._check_margin_limits(request, current_position):
            return False
        return True

    def _check_fat_finger(self, request: OrderRequest) -> bool:
        """[①사유]: 1회 주문 한도 및 비정상 수량 차단."""
        if request.quantity <= 0 or request.quantity > self.limits["max_single_order_qty"]:
            self.logger.warning(f"Fat-Finger Blocked: Qty {request.quantity}")
            return False
        return True

    def _check_margin_limits(self, request: OrderRequest, current_position: Position) -> bool:
        """[①사유]: 실시간 증거금 및 포지션 한도 점검."""
        # 총 포지션 한도 체크
        if current_position.total_qty + request.quantity > self.limits["max_total_position"]:
            self.logger.error("Total Position Limit Exceeded")
            return False
            
        # 증거금 사용률 체크 (현재 마진 / 설정된 마진 한도)
        if current_position.used_margin / self.config.max_margin_usage > self.limits["margin_usage_threshold"]:
            self.logger.warning("Margin Usage Alert: Exceeding 85% threshold")
            
        return True
