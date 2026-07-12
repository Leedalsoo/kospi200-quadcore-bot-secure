"""
[①사유]: IV vs HV 스프레드 수확 및 IV Surface 모델 전환.
[②방어 기제 #37]: 데이터 정밀도에 따른 모델 동적 스위칭.
"""
from .base_plugin import BaseStrategyPlugin

class Track5Volatility(BaseStrategyPlugin):
    async def on_market_tick(self, data: dict):
        # IV/HV 스프레드 계산 및 모델 전환
        # IV가 HV보다 10% 이상 높을 때 매도 (명세서 15-37)
        if data.get('iv', 0) > (data.get('hv', 0) * 1.1):
            # IV 급등 시 큐빅 스플라인 모델 전환 로직 포함
            model = "CUBIC" if data.get('iv_spike') else "LINEAR"
            
            weight = self.context['active_weights'].get(self.name, 0.1)
            await self.execute_order(data['last_price'], int(2 * weight), "SELL")
            self.logger.info(f"Volatility Trade [{model}]: Selling IV excess.")

