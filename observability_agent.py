"""
[①사유]: 하드웨어 리소스 감시 및 시스템 성능 메트릭 통합 관제.
[②방어 기제 #3, #53, #10]: 하드웨어 임계치 감시 및 성능 지표 로그화.
"""

import logging
import psutil
from datetime import datetime

class ObservabilityAgent:
    def __init__(self, alert_threshold_cpu: float = 80.0):
        self.alert_threshold_cpu = alert_threshold_cpu
        self.logger = logging.getLogger("ObservabilityAgent")

    def collect_metrics(self) -> dict:
        """[①사유]: 시스템 리소스 및 성능 지표 동시 수집."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "timestamp": datetime.now().isoformat()
        }

    def log_metric(self, name: str, value: float, unit: str):
        """[①사유]: 전략적 운영 지표(Latency 등) 기록."""
        self.logger.info(f"METRIC | {name} | {value} {unit}")

    def check_health(self):
        """[①사유]: 하드웨어 건전성 감시 및 경보."""
        metrics = self.collect_metrics()
        
        # 하드웨어 임계치 방어 기제
        if metrics["cpu_percent"] > self.alert_threshold_cpu:
            self.logger.critical(f"HEALTH ALERT: CPU {metrics['cpu_percent']}% > Threshold {self.alert_threshold_cpu}%")
            return False # 시스템 보호를 위한 신호
            
        return True
