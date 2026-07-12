"""
[①사유]: 변동성 스큐 및 시간가치 차익거래.
[②방어 기제 #102, #158]: 비대칭 레깅(Asymmetric Legging-in)을 통한 유동성 확보.
"""
from .base_plugin import BaseStrategyPlugin

class Track3Arbitrage(BaseStrategyPlugin):
    async def on_market_tick(self, data: dict):
        # 괴리율 0.5% 이상 발생 시 (명세서 10-4)
        if abs(data.get('basis_spread', 0)) > 0.005:
            # 비대칭 레깅 진입 시퀀스
            # 1. 유동성이 얇은 OTM(외가격) 옵션에 선행 지정가 제출
            await self.execute_order(data['otm_price'], 1, "SELL")
            
            # 2. 찰나의 순간 유동성 풍부한 ATM(등가격) 옵션 타격
            await self.execute_order(data['atm_price'], 1, "BUY")
            
            self.logger.info("Arbitrage Legging-in sequence completed.")

