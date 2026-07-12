"""
[①사유]: 시장 변동성 연동형 동적 데드밴드 헤징.
[②방어 기제 #147]: 수익 확정 및 감마 노출도 관리.
"""
from .base_plugin import BaseStrategyPlugin

class Track4Gamma(BaseStrategyPlugin):
    async def on_market_tick(self, data: dict):
        # 실현변동성(RV)에 따른 데드밴드 동적 확장 (명세서 11-2)
        rv = data.get("realized_volatility", 0.3)
        band = max(0.2, min(0.6, rv * 2.0))
        
        # 감마 노출에 따른 델타 밴드 이탈 시 헤징
        if abs(data.get('delta', 0)) > band:
            side = "SELL" if data['delta'] > 0 else "BUY"
            weight = self.context['active_weights'].get(self.name, 0.1)
            
            # 선물 헤지 주문 발송
            await self.execute_order(data['last_price'], int(1 * weight), side)
            self.logger.info(f"Gamma Scalping Hedge: {side} @ {data['last_price']}")

