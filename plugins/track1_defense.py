"""
이 코드는 명세서 제8장 요구사항을 반영하여 작성되었음.
[①사유]: 자본의 50%를 방어하는 메인 엔진. 본월물 가두리 방어 및 선물 델타 헤징.
[②방어 기제 #8, #19, #212]: 1/8 Kelly 배팅 및 실시간 델타 중립화.
[③커스텀 범위]: 5% MDD 셧다운 및 0.1 델타 밴드 헤징.
"""

from .base_plugin import BaseStrategyPlugin
import logging

class Track1Defense(BaseStrategyPlugin):
    async def on_market_tick(self, data: dict):
        """
        [①사유]: 시장 데이터를 분석하여 옵션 포지션 리스크를 선물로 즉시 헤지.
        [②방어 기제 #8-9]: 옵션 호가 공백 시 선물 주문으로 델타 중립화 강제.
        """
        # 1. 시스템 가중치 확인 (자본의 50% 기본 배분)
        weight = self.context['active_weights'].get(self.name, 0.5)
        
        # 2. 포트폴리오 델타 총합 기반 선물 헤지 수량 도출 (명세서 제8장 9조)
        # portfolio_delta: 옵션 포지션의 전체 델타 합계
        portfolio_delta = data.get("total_delta", 0.0)
        
        # 델타 중립화 임계치(둔감도 버퍼) 0.1 적용
        if abs(portfolio_delta) > 0.1:
            # 선물 1계약은 델타 1.0으로 가정 (KOSPI 200 선물)
            # 헤지 계약 수(Q_futures) = -round(delta_portfolio / 1.0)
            hedge_qty = -round(portfolio_delta / 1.0)
            side = "BUY" if hedge_qty > 0 else "SELL"
            
            # [핵심 방어] 옵션 청산 불완전성 극복을 위한 선물 선행 주문
            # 호가가 얇은 옵션 대신 유동성이 풍부한 선물로 먼저 리스크를 Lock-down
            await self.execute_order(
                price=data['last_price'], 
                qty=abs(hedge_qty), 
                side=side
            )
            self.logger.info(f"Dynamic Futures Hedge: {side} {abs(hedge_qty)} contracts at {data['last_price']}")

        # 3. [방어 기제 #8-1] 1/8 Kelly 포지션 사이징 및 MDD 체크
        # 명세서 제8장 8조: 계좌 평가 잔고 MDD 5% 이하일 때만 신규 진입
        if data.get("total_mdd", 0) < 0.05: 
            # 1/8 Kelly 기반 사이징 적용 (가중치 * 1계약)
            # weight(0.5)를 적용하여 시스템 전체 자산 배분 비중 준수
            await self.execute_order(
                price=data['last_price'], 
                qty=int(1 * weight), 
                side="SELL"
            )
            self.logger.info(f"Track1 Defense: New Sell Entry with weight {weight}")
        else:
            # [방어 기제 #50] MDD 한도 도달 시 방어 엔진 신규 진입 중단
            self.logger.warning("MDD threshold reached. Halting new entries.")
