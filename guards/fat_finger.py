"""
이 코드는 명세서 제13장 리스크 관리 및 방어 기제 요구사항을 반영하여 작성되었음.
[①사유]: 주문 수량 및 가격 입력 오류(Fat-Finger)로 인한 치명적 손실 방지.
[②위험성]: 시장 충격 비용(Market Impact) 발생 및 의도치 않은 대규모 포지션 진입.
[③커스텀 범위]: 주문 수량 및 가격 상/하한선 하드코딩 필터.
"""

from data_contract import OrderRequest, HardLimitsConfig

class FatFingerGuard:
    """
    [①사유]: 주문 요청 데이터의 논리적 유효성 즉시 검증.
    [방어 기제 #36, #165] 범위 이탈 주문 원천 차단.
    """
    def __init__(self, config: HardLimitsConfig):
        self.config = config

    def check(self, request: OrderRequest) -> bool:
        """
        [①사유]: 가격 및 수량 상한선 검증.
        [②위험성]: 필터 우회 시 계좌 증거금 초과 및 시장 교란.
        """
        # 수량 검증: 일회 주문 한도 체크
        if request.qty > self.config.max_order_qty_per_trade:
            return False
            
        # 가격 검증: 현재 시장가 대비 % 편차 확인 (예: 5% 이상 이탈 시 차단)
        price_deviation = abs(request.price - request.last_price) / request.last_price
        if price_deviation > self.config.max_price_deviation_pct:
            return False
            
        return True

