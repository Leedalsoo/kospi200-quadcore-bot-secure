"""
시스템 전체의 시간 동기화 및 거래소 일정 관리 엔진
[①사유]: 모든 에이전트 간 동일한 타임스탬프 기준 확보 및 시장 운영시간 판정.
[②위험성]: 에이전트마다 시간이 다를 경우(Drift), 이벤트 순서 뒤바뀜으로 주문 논리 오류 발생.
"""

from datetime import datetime, time
import pytz

class TimeAgent:
    """
    [①사유]: 표준 시간(KST) 유지 및 장 운영 상태 체크.
    [방어 기제 #8, #131] 시간 Drift 방지 및 장 시작/종료 상태 제어.
    """
    def __init__(self):
        self.tz = pytz.timezone('Asia/Seoul')
        # KRX 장 운영 시간 설정 (예시)
        self.market_open = time(9, 0)
        self.market_close = time(15, 30)

    def get_now(self) -> datetime:
        """[①사유]: 시스템 전체 표준 KST 시간 반환."""
        return datetime.now(self.tz)

    def is_market_open(self) -> bool:
        """
        [①사유]: 장 운영 시간 판정.
        [방어 기제 #131] 비정상적인 시간대 주문 집행 원천 차단.
        """
        now_time = self.get_now().time()
        return self.market_open <= now_time <= self.market_close

