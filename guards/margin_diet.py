"""
이 코드는 명세서 제13장 리스크 관리 및 계좌 보호 요구사항을 반영하여 작성되었음.
[①사유]: 계좌 증거금 소진 방지 및 MDD(Maximum Drawdown) 하드 제한.
[②위험성]: 포지션 누적 시 마진콜 발생 및 계좌 전액 손실 위험.
[③커스텀 범위]: 실시간 마진 레벨 및 손실 한도 검사.
"""

from data_contract import Position, HardLimitsConfig

class MarginDietGuard:
    """
    [①사유]: 실시간 마진 레벨 모니터링 및 생존 한도 제어.
    [방어 기제 #50, #153, #212] 손실 한도 돌파 시 셧다운.
    """
    def __init__(self, config: HardLimitsConfig):
        self.config = config

    def check_safety(self, position: Position) -> bool:
        """
        [①사유]: 계좌 전체 증거금 안전성 확인.
        [②위험성]: 리스크 체크 누락 시 마진콜까지 강제 보유.
        """
        # 1. 일일 손실 한도 체크
        if position.unrealized_pnl < -self.config.max_daily_loss_amount:
            return False
            
        # 2. 증거금 유지비율(Maintenance Margin) 체크
        if position.margin_level < self.config.min_margin_level:
            return False
            
        return True

