"""
이 코드는 명세서 제10장 시스템 관제 요구사항을 반영하여 작성되었음.
[①사유]: 실시간 시스템 건전성 모니터링 및 성능 병목 식별.
[②위험성]: 관제 실패 시 시스템 장애 인지 지연 및 대응 불가능.
[③커스텀 범위]: 메트릭 수집 및 임계치 알람 처리.
"""

import psutil
import logging
from datetime import datetime

class ObservabilityAgent:
    """
    [①사유]: 하드웨어 및 프로세스 성능 모니터링.
    [방어 기제 #3, #53] 시스템 가용성 유지.
    """
    def __init__(self, alert_threshold_cpu: float = 80.0):
        self.alert_threshold_cpu = alert_threshold_cpu
        self.logger = logging.getLogger("Observability")

    def collect_metrics(self) -> dict:
        """[①사유]: 실시간 메트릭 수집. [②위험성]: 모니터링 연산 자체가 매매 지연을 유발함."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "timestamp": datetime.now().isoformat()
        }

    def check_health(self):
        """
        [①사유]: 비정상 상태 식별 및 경보 발령.
        [방어 기제 #17] Severity 수준별 알림.
        """
        metrics = self.collect_metrics()
        # [방어 기제 #147] CPU 점유율 임계치 감시
        if metrics["cpu_percent"] > self.alert_threshold_cpu:
            self.logger.warning(f"CRITICAL: High CPU usage: {metrics['cpu_percent']}%")
            # 향후 SMS/Webhook 알림 연동 및 Kill Switch 호출

