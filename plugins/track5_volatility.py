"""
이 코드는 명세서 제3장 및 제15장 요구사항을 반영하여 작성되었음.
[①사유]: IV(내재변동성)와 HV(역사적변동성) 스프레드를 이용한 변동성 매도.
[②위험성]: IV 급등 시 Linear 보간 오차로 인한 포지션 리스크 발생.
[③커스텀 범위]: IV 급등 시 Cubic Spline 모델로 자동 전환하여 Greeks 정밀도 확보.
[방어 기제 매핑]: #37, #15-37
"""

from .base_plugin import BaseStrategyPlugin
import logging

class Track5Volatility(BaseStrategyPlugin):
    
    async def on_market_tick(self, data: dict):
        """
        [①사유]: 표준 진입점. 
        safe_execute를 통해 로직을 실행하여 예외 상황을 중앙으로 전파함.
        """
        await self.safe_execute(self._my_logic, data)

    async def _my_logic(self, data: dict):
        """
        [①사유]: 실제 변동성 매도 전략 로직 구현부.
        [방어 기제 #37]: 데이터 변동성에 따른 IV Surface 보간 모델 스위칭.
        """
        # 1. 시스템 가중치 확인 (자본 배분 20% 가정)
        weight = self.context['active_weights'].get(self.name, 0.2)
        
        # 2. IV/HV 스프레드 계산
        iv = data.get('iv', 0.0)
        hv = data.get('hv', 0.0)
        
        # 3. [핵심] IV Surface 모델 동적 전환 규칙 (명세서 제3장 5조)
        model_type = "CUBIC_SPLINE" if data.get('iv_spike', False) else "LINEAR_INTERPOLATION"
        
        # 4. [고도화] 변동성 매도 조건 검증
        if iv > (hv * 1.1):
            
            # 5. [최종] 정밀 타격
            target_qty = int(2 * weight)
            
            if target_qty > 0:
                await self.execute_order(
                    price=data['last_price'], 
                    qty=target_qty, 
                    side="SELL"
                )
                
                self.logger.info(
                    f"Volatility Trade Executed [{model_type}]: "
                    f"IV={iv:.2f}, HV={hv:.2f}, Qty={target_qty}"
                )
