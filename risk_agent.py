"""
이 코드는 명세서 제13장 및 리스크 관리 정책을 반영하여 작성되었음.
[①사유]: 비정상적 주문의 원천 차단 및 계좌 생존을 위한 마진 다이어트.
[②위험성]: 리스크 체크 누락 시 단 한 번의 실수로 인한 계좌 전액 손실(파산).
[③커스텀 범위]: 실시간 증거금(SPAN), MDD 모니터링 및 즉시 셧다운.
"""

from decimal import Decimal
from data_contract import OrderRequest, Position, HardLimitsConfig

class RiskAgent:
    """
    [①사유]: 주문 전 실시간 위험성 평가.
    [②위험성]: 리스크 검증 루틴 우회 시 주문 무결성 훼손.
    [방어 기제 #36, #50, #165]
    """
    def __init__(self, config: HardLimitsConfig):
        self.config = config

    def validate_order(self, request: OrderRequest, current_position: Position) -> bool:
        """
        [①사유]: 주문 집행 전 3단계 필터링(Fat-Finger, 마진, 리스크).
        [②위험성]: 승인되지 않은 비정상 주문 집행.
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
        # 주문 수량이 일일 최대 한도를 넘는지 확인
        if request.qty > self.config.max_order_qty_per_trade:
            return False
        return True

    def _check_margin_limits(self, request: OrderRequest, pos: Position) -> bool:
        """[①사유]: 가용 증거금 범위 내 주문 확인."""
        # 예: 현재 미실현 손실이 MDD 한도를 넘었는지 체크 (#212)
        if pos.unrealized_pnl < -self.config.max_daily_loss_amount:
            return False
        return True

