"""
이 코드는 명세서 제3장 및 제12장 7조의 요구사항을 반영하여 작성되었음.
[①사유]: 시장 운영 시간 외 발주 방지 및 이벤트 로그의 타임스탬프 동기화.
[②위험성]: 시각 역행 시 주문 로직 오류 및 시스템 정지.
[③커스텀 범위]: Asia/Seoul 타임존 기반 Watchdog 로직.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo
import time as std_time

class WatchdogTimeAgent:
    """
    [①사유]: P99 Latency 측정 및 시장 시간 하드 가드.
    [②위험성]: 시스템 시간 왜곡 시 발생할 수 있는 매매 오작동.
    """
    def __init__(self):
        self.kst = ZoneInfo("Asia/Seoul")
        self.market_open = time(8, 45)
        self.market_close = time(15, 45)

    def get_current_kst(self) -> datetime:
        """[①사유]: KST 기준 절대 시간 반환. [②위험성]: Naive 시각 사용 방지."""
        return datetime.now(self.kst)

    def get_monotonic_time(self) -> float:
        """[①사유]: 시스템 연산 지연율 측정. [②위험성]: 시각 동기화 시 역행 방지."""
        return std_time.monotonic()

    def check_market_open(self) -> bool:
        """[①사유]: 장 운영 시간 외 거래 차단. [②위험성]: 임의 시간 거래 시 리스크 노출."""
        now = self.get_current_kst()
        if now.weekday() >= 5: # 토, 일요일 차단
            return False
        return self.market_open <= now.time() <= self.market_close

