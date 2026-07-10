"""
이 코드는 명세서 제9장 및 기능 제어 요구사항을 반영하여 작성되었음.
[①사유]: 런타임 중 특정 알고리즘/기능의 즉시 격리(Isolation) 및 활성화.
[②위험성]: 특정 기능 오작동 시 전체 시스템 정지(Cold Restart) 상황 발생.
[③커스텀 범위]: 전략 모듈별 상태 플래그 관리 및 런타임 제어.
"""

class FeatureFlagAgent:
    """
    [①사유]: 시스템 기능별 실시간 ON/OFF 스위치.
    [방어 기제 #80, #190] 특정 기능 비활성화를 통한 리스크 회피.
    """
    def __init__(self):
        # 시스템 초기값: 모든 기능 활성화
        self._flags = {
            "auto_trading": True,
            "gamma_hedging": True,
            "arbitrage_engine": True
        }

    def set_flag(self, feature: str, enabled: bool):
        """[①사유]: 런타임 기능 제어. [②위험성]: 비정상 상태 진입."""
        if feature in self._flags:
            self._flags[feature] = enabled
            # 여기에 변경 사항을 이벤트 버스로 전송하여 에이전트들이 즉시 반영하게 함

    def is_enabled(self, feature: str) -> bool:
        """[①사유]: 특정 전략/기능 실행 전 체크."""
        return self._flags.get(feature, False)

