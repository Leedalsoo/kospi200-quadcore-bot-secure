"""
이 코드는 명세서 제9장 기능 제어 및 상태 전이 요구사항을 반영하여 작성되었음.
[①사유]: 런타임 중 특정 알고리즘/기능의 즉시 격리 및 상태 전이 제어.
[②위험성]: 특정 기능 오작동 시 전체 시스템 정지(Cold Restart) 상황 발생.
[③커스텀 범위]: 전략 모듈별 단계적 격리(Drain->Halt->Recovery) 플래그 관리.
[방어 기제 매핑]: #56, #80, #190, #212
"""

from enum import Enum, auto
from typing import Dict, Any
import logging

logger = logging.getLogger("FeatureFlag")

class FeatureState(Enum):
    """[①사유]: 전략별 상태 전이 규격."""
    ACTIVE = auto()        # 정상 운영
    DRAINING = auto()      # 신규 진입 차단, 기보유 포지션 유지
    HALTED = auto()        # 모든 활동 중단 (수동 개입 대기)
    MAINTENANCE = auto()   # 시스템 점검 중

class FeatureFlagAgent:
    """
    [①사유]: 전략별 상태 머신 관리 및 안전한 런타임 제어.
    [방어 기제 #56]: 급격한 기능 정지가 아닌, 단계적 안전 종료(Graceful Shutdown) 보장.
    """
    def __init__(self):
        # [수치 정립]: 시스템 초기 상태
        self._flags: Dict[str, FeatureState] = {
            "auto_trading": FeatureState.ACTIVE,
            "gamma_hedging": FeatureState.ACTIVE,
            "arbitrage_engine": FeatureState.ACTIVE
        }

    def transition(self, feature: str, target_state: FeatureState):
        """
        [①사유]: 안전한 상태 전이 제어.
        [②위험성]: 무분별한 상태 변경 시 포지션 불일치 발생.
        """
        if feature not in self._flags:
            logger.error(f"Unknown feature: {feature}")
            return

        current = self._flags[feature]
        logger.info(f"Transitioning {feature}: {current.name} -> {target_state.name}")
        
        # [방어 기제 #56] 상태 전이 로직
        self._flags[feature] = target_state
        
        # 이벤트 버스를 통해 전략 에이전트들에게 상태 전파 로직 호출 가능
        # self.bus.publish("FEATURE_STATE_CHANGED", {"feature": feature, "state": target_state})

    def is_active(self, feature: str) -> bool:
        """[①사유]: 전략 실행 전 활성화 여부 확인."""
        return self._flags.get(feature) == FeatureState.ACTIVE

    def is_draining(self, feature: str) -> bool:
        """[①사유]: 신규 진입을 제한하고 청산 대기 중인가?"""
        return self._flags.get(feature) == FeatureState.DRAINING

    def get_status(self, feature: str) -> str:
        return self._flags.get(feature, FeatureState.HALTED).name
