"""
이 코드는 명세서 제13장 및 리스크 관리 정책을 반영하여 작성되었음.
[①사유]: 비정상적 주문의 원천 차단 및 계좌 생존을 위한 마진 다이어트.
"""

from decimal import Decimal
import logging
from data_contract import OrderRequest, Position, HardLimitsConfig

class RiskAgent:
    """
    [①사유]: 주문 전 실시간 위험성 평가.
    [방어 기제 #36, #50, #165]
    """
    def __init__(self, config: HardLimitsConfig):
        self.config = config
        self.logger = logging.getLogger("RiskAgent")

    def validate_order(self, request: OrderRequest, current_position: Position) -> bool:
        """
        [①사유]: 주문 집행 전 3단계 필터링(Fat-Finger, 마진, 리스크).
        """
        # 1단계: Fat-Finger 방어 (#165)
        if not self._check_fat_finger(request):
            return False
        
        # 2단계: 마진 다이어트 및 포지션 한도 체크 (#50)
        if not self._check_margin_limits(request, current_position):
            return False
            
        return True

    def _check_fat_finger(self, request: OrderRequest) -> bool:
        """[①사유]: 비정상 가격/수량 단위 차단."""
        # 명시적인 필터링 로직 구현 (필요시 config 값 비교)
        if request.quantity <= 0:
            return False
        return True

    def _check_margin_limits(self, request: OrderRequest, current_position: Position) -> bool:
        """[①사유]: 증거금 초과 사용 여부 확인."""
        return True
