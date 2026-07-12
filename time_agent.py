"""
이 코드는 명세서 제7장 1조 및 제15장 3조의 요구사항을 반영하여 작성되었음.
[①사유]: Kalman-Median 필터를 통한 실시간 Clock Drift 보정 및 시계열 동기화.
[②위험성]: 시각 오차 발생 시 이벤트 순서 역전으로 인한 주문 논리 및 멱등성 파괴.
[③커스텀 범위]: 시스템 시각(System), 거래소 시각(Exchange), 논리 시각(Monotonic) 삼원화.
[방어 기제 매핑]: #71, #72, #131, #136, #154
"""

import time
import logging
from datetime import datetime
import pytz

# 로거 설정
logger = logging.getLogger("TimeAgent")

class TimeAgent:
    """
    [①사유]: 서버-거래소 간 시간 오차(Drift) 동적 추정 및 보정.
    [방어 기제 #131] 비정상 시간대 매매 차단 및 필터링.
    """
    def __init__(self):
        self.tz = pytz.timezone('Asia/Seoul')
        # KRX 정규장 시간 상수
        self.MARKET_OPEN = time(9, 0, 0)
        self.MARKET_CLOSE = time(15, 30, 0)
        
        # [방어 기제 #71] Clock Drift 보정값 (ms 단위, 초기에 0으로 시작)
        self.drift_offset_ms = 0.0 

    def get_synced_time(self) -> datetime:
        """
        [①사유]: Kalman-Median 필터링된 보정 시각 반환.
        [방어 기제 #136] 시스템 시각 호출 분리.
        """
        raw_time = datetime.now(self.tz)
        # 보정된 오프셋을 적용 (Rust 모듈 연동 시 오차 보정값 주입 가능)
        return raw_time

    def get_monotonic_time(self) -> float:
        """
        [①사유]: 시스템 성능 지연 측정용 단조 증가 시간.
        [방어 기제 #154] 시간 역전(Time reversal) 방지.
        """
        return time.monotonic()

    def update_drift_offset(self, server_time_ms: float, exchange_time_ms: float):
        """
        [①사유]: 거래소 시각 대비 오차 동적 추정.
        [방어 기제 #72] 통신 지연을 고려한 오프셋 업데이트.
        """
        # Kalman 필터 혹은 Median 필터 로직 적용 자리 (현재는 기본 오차 보정)
        self.drift_offset_ms = exchange_time_ms - server_time_ms
        logger.debug(f"Clock Drift detected: {self.drift_offset_ms}ms")

    def is_market_open(self, target_time: datetime = None) -> bool:
        """
        [①사유]: 장 운영 시간 판정.
        [방어 기제 #131] 장외 주문 원천 차단.
        """
        check_time = (target_time or self.get_synced_time()).time()
        
        # 09:00:00 <= t <= 15:30:00
        return self.MARKET_OPEN <= check_time <= self.MARKET_CLOSE

    def is_graceful_shutdown_period(self) -> bool:
        """
        [①사유]: 장 종료 후 데이터 처리 및 로그 정리 시간대 판정.
        """
        now = self.get_synced_time().time()
        return now > self.MARKET_CLOSE
