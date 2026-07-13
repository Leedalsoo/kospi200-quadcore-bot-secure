"""
이 코드는 명세서 제9장 및 기억 속의 '선물 헤징 결합' 요구사항을 반영하여 작성되었음.
[①사유]: 함정 전략(Trap) 진입 시 발생하는 델타 노출도를 선물로 즉시 중립화.
[②위험성]: 기습 진입 직후의 변동성 휩쏘로 인한 함정 비용(프리미엄) 전액 손실 방지.
[③커스텀 범위]: 선물 헤지 비율 동기화, 휩쏘 필터 결합, 15분 쿨다운 강제.
[방어 기제 매핑]: #9-3, #155, #222
"""

from .base_plugin import BaseStrategyPlugin
import time

class Track2Trap(BaseStrategyPlugin):
    def __init__(self, name: str, event_bus, shared_context):
        super().__init__(name, event_bus, shared_context)
        self.last_trade_time = 0
        self.COOLDOWN_SECONDS = 900 # 15분 하드웨어 쿨다운 (명세서 9-5)

    async def on_market_tick(self, data: dict):
        """
        [①사유]: 표준 진입점. 전략 로직은 _my_logic()에서 실행하며, 
        safe_execute를 통해 에러 발생 시 중앙 시스템으로 즉시 전파함.
        """
        await self.safe_execute(self._my_logic, data)

    async def _my_logic(self, data: dict):
        """
        [①사유]: 실제 전략 로직 구현부. 
        [방어 기제]: 4중 필터 통과 후 옵션 기습 진입 및 즉각적 선물 헤지(Delta-Neutral).
        """
        # 1. 쿨다운 검증
        if time.monotonic() - self.last_trade_time < self.COOLDOWN_SECONDS:
            return

        # 2. 4중 휩쏘 필터 (OBI, Basis, Skew, POC)
        if all([data.get('obi', 0) > 0.5, data.get('basis_valid'), 
                data.get('skew_match'), data.get('poc_break')]):
            
            weight = self.context['active_weights'].get(self.name, 0.1)
            target_qty = int(10 * weight)
            
            # 3. [핵심] 옵션 기습 진입 (함정 설치)
            await self.execute_order(data['last_price'], target_qty, "BUY")
            
            # 4. [핵심] 선물 헤지 (함정 비용 보호)
            # 옵션 진입으로 인해 발생한 델타를 선물로 즉시 상쇄
            option_delta = data.get("option_delta_exposure", 0.0)
            hedge_qty = -round(option_delta) 
            
            if abs(hedge_qty) > 0:
                side = "SELL" if hedge_qty < 0 else "BUY"
                await self.execute_order(data['last_price'], abs(hedge_qty), side)
                self.logger.info(f"Trap Secured: Option Buy & Futures Hedge {side} {abs(hedge_qty)}")

            self.last_trade_time = time.monotonic()
            self.logger.info(f"Trap Strategy Triggered: {target_qty} units with Futures Hedge active.")
