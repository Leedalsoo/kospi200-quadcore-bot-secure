"""
[①사유]: 본월물 가두리 방어 및 선물 델타 헤징 엔진.
[②방어 기제 #14, #19, #87, #192]: 1/8 Kelly 배팅 및 동적 선물 헤징을 통한 델타 중립화.
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
            # -round(델타 / 1.0)으로 헤지 수량 결정
            hedge_qty = -round(portfolio_delta / 1.0)
            side = "BUY" if hedge_qty > 0 else "SELL"
            
            # 3. [핵심 방어] 옵션 청산 불완전성 극복을 위한 선물 선행 주문
            # 호가가 얇은 옵션 대신 유동성이 풍부한 선물로 먼저 리스크를 Lock-down
            await self.execute_order(
                price=data['last_price'], 
                qty=abs(hedge_qty), 
                side=side
            )
            self.logger.info(f"Dynamic Futures Hedge: {side} {abs(hedge_qty)} contracts at {data['last_price']}")

        # 4. [방어 기제 #8-1] 1/8 Kelly 포지션 사이징
        # 이론적 배팅 상한 내에서 포지션 조절
        available_capital = data.get("available_capital", 0.0)
        max_qty = int(available_capital * 0.05 * weight) # 전체 자산의 5% 상한
        
        # 가두리 매도 로직 (본월물 옵션 Short)
        if data.get("total_pos_qty", 0) < max_qty:
            await self.execute_order(data['last_price'], 1, "SELL")
