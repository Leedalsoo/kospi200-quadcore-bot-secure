"""
이 코드는 명세서 제13장 데이터 무결성 및 상식 검증 요구사항을 반영하여 작성되었음.
[①사유]: 비정상적 수치(Zero, Negative) 유입으로 인한 매매 엔진 연산 오류 방지.
[②위험성]: 가격 0원 입력 시 계산 오류(Divide by Zero)로 시스템 크래시 발생.
[③커스텀 범위]: 데이터 타입 및 값의 허용 범위 강제 검사.
"""

from data_contract import OrderRequest, MarketTick

class SanityCheckGuard:
    """
    [①사유]: 데이터가 시스템 로직으로 들어가기 전 '상식' 검증.
    [방어 기제 #35, #116] 범위 이탈 데이터 즉시 거부.
    """
    
    @staticmethod
    def is_valid_price(price: float) -> bool:
        """[①사유]: 가격은 반드시 양수여야 함."""
        return price > 0

    @staticmethod
    def is_valid_qty(qty: int) -> bool:
        """[①사유]: 수량은 반드시 자연수여야 함."""
        return qty > 0

    def check_market_data(self, tick: MarketTick) -> bool:
        """[①사유]: 호가창 데이터 무결성 검증."""
        return self.is_valid_price(tick.bid) and self.is_valid_price(tick.ask)

