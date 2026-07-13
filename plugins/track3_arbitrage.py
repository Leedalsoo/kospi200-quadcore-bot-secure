"""
이 코드는 명세서 제10장 및 제11장 요구사항을 반영하여 작성되었음.
[①사유]: Z-Score 기반 통계적 차익거래 및 비대칭 레깅(Asymmetric Legging) 집행.
[②위험성]: 레깅 진입 시 유동성 부족으로 인한 손실 방지.
[③커스텀 범위]: Z-Score +/- 2.0 임계치, 0.5% 괴리율 기반 기계적 집행.
[방어 기제 매핑]: #102, #158, #165
"""
from .base_plugin import BaseStrategyPlugin

class Track3Arbitrage(BaseStrategyPlugin):
    
    async def on_market_tick(self, data: dict):
        """
        [①사유]: 표준 진입점. 전략 로직은 _my_logic()에서 실행하며, 
        safe_execute를 통해 에러 발생 시 중앙 시스템으로 즉시 전파함.
        """
        await self.safe_execute(self._my_logic, data)

    async def _my_logic(self, data: dict):
        """
        [①사유]: 실제 통계적 차익거래 전략 로직 구현부.
        """
        # 1. 시스템 공유 컨텍스트에서 전체 자본 배분 확인
        weight = self.context['active_weights'].get(self.name, 0.2)
        
        # 2. 통계적 지표 수치화 (Z-Score)
        z_score = data.get("z_score", 0.0) 
        basis_spread = data.get("basis_spread", 0.0)
        
        # 3. [핵심 로직] 통계적 확률에 기반한 기계적 진입
        if abs(basis_spread) > 0.005 and abs(z_score) > 2.0:
            
            # 비대칭 레깅 알고리즘
            side_otm = "SELL" if basis_spread > 0 else "BUY"
            side_atm = "BUY" if side_otm == "SELL" else "SELL"
            
            # OTM 호가창에 먼저 선행 지정가 발주
            await self.execute_order(data['otm_price'], int(1 * weight), side_otm)
            
            # ATM 호가창에 즉시 타격 주문
            await self.execute_order(data['atm_price'], int(1 * weight), side_atm)
            
            self.logger.info(f"Arbitrage Trade Executed: Z={z_score:.2f}, Spread={basis_spread:.4f}")
            
        # 4. 긴급 손절 (명세서 10-2)
        if abs(z_score) > 4.0:
            # 수량 0으로 설정하여 전체 청산 명령 발행
            await self.execute_order(data['last_price'], 0, "CLOSE_ALL")
            self.logger.critical("Statistical Arbitrage Emergency Exit: Z-Score Divergence")
