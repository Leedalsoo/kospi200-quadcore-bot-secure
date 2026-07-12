"""
[①사유]: 볼륨 폭발 및 비대칭 추세 포착을 위한 기습 진입.
[②방어 기제 #155, #222]: 4중 필터(OBI, Basis, Skew, POC) 교차 검증 적용.
"""
from .base_plugin import BaseStrategyPlugin

class Track2Trap(BaseStrategyPlugin):
    async def on_market_tick(self, data: dict):
        # 4중 휩쏘 필터링 로직 (명세서 9-2)
        # 1. OBI(호가 잔량 불균형), 2. 베이시스 검증, 3. 스큐(Skew) 일치, 4. POC(매물대) 관통
        filters = [
            data.get('obi', 0) > 0.5,
            data.get('basis_valid', False),
            data.get('skew_match', False),
            data.get('poc_break', False)
        ]
        
        if all(filters):
            # 자본의 10% 할당 제약 내에서 가중치 반영
            weight = self.context['active_weights'].get(self.name, 0.1)
            # 기습 진입 (지정가 펀칭)
            await self.execute_order(data['last_price'], int(10 * weight), "BUY")
            self.logger.info(f"Trap Strategy Triggered: {data['last_price']}")

