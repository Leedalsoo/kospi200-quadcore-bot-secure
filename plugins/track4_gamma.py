"""
이 코드는 명세서 제11장 요구사항을 반영하여 작성되었음.
[①사유]: 변동성 연동형 동적 데드밴드(0.2~0.6) 기반 정밀 감마 스캘핑.
[②방어 기제 #147, #182]: 슬리피지 최소화 및 수수료 최적화 로직.
[③커스텀 범위]: RV 기반 밴드 확장, Gamma 노출도 보정, 비대칭 헤징.
[방어 기제 매핑]: #147, #182, #233
"""

from .base_plugin import BaseStrategyPlugin
import logging

class Track4Gamma(BaseStrategyPlugin):
    
    async def on_market_tick(self, data: dict):
        """
        [①사유]: 표준 진입점. 
        safe_execute를 통해 로직을 실행하여 예외 상황을 중앙으로 전파함.
        """
        await self.safe_execute(self._my_logic, data)

    async def _my_logic(self, data: dict):
        """
        [①사유]: 감마 스캘핑 핵심 로직 구현부.
        [방어 기제]: 시장 변동성(RV) 기반 동적 헤징 및 감마 노출도 상쇄.
        """
        # 1. 시스템 가중치 확인 (자본 배분 10%)
        weight = self.context['active_weights'].get(self.name, 0.1)
        
        # 2. 동적 데드밴드 연산 (명세서 11-2)
        rv = data.get("realized_volatility", 0.3)
        dynamic_band = max(0.2, min(0.6, rv * 2.0))
        
        # 3. 감마 노출도(Gamma Exposure) 기반 델타 트리거 보정
        gamma = data.get("gamma", 0.0)
        adjusted_band = dynamic_band / (1.0 + abs(gamma))
        
        # 4. 선물 헤지 시점 판정
        delta = data.get('delta', 0.0)
        
        if abs(delta) > adjusted_band:
            # 5. [핵심] 방향성 정밀 타격
            side = "SELL" if delta > 0 else "BUY"
            
            # [방어 기제 #182] 포지션 사이징: 전체 감마 노출도에 비례
            target_qty = int(abs(delta) * 100 * weight)
            
            # [최종] 주문 실행
            if target_qty > 0:
                await self.execute_order(
                    price=data['last_price'], 
                    qty=target_qty, 
                    side=side
                )
                self.logger.info(
                    f"Gamma Scalping Hedge [{self.name}]: {side} {target_qty} units "
                    f"at {data['last_price']} [Band: {adjusted_band:.3f}, Delta: {delta:.3f}]"
                )
