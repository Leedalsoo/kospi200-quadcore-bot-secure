"""
이 코드는 명세서 제3장 11조 및 제7장 4조의 요구사항을 반영하여 작성되었음.
[①사유]: 설정값의 안전한 로딩, 스키마 검증 및 런타임 변경(Hot Reload) 제어.
[②위험성]: 잘못된 설정값 주입으로 인한 매매 엔진 오작동 및 전략 파산.
[③커스텀 범위]: Hot/Cold 설정 분리, 스키마 검증, 런타임 무결성 보호.
[방어 기제 매핑]: #102, #111, #126, #172, #193
"""

import json
import logging
import os
from typing import Any, Dict, Set

# 로거 설정
logger = logging.getLogger("ConfigAgent")

class ConfigAgent:
    """
    [①사유]: 설정값의 안전한 로딩 및 런타임 무결성 검사.
    [방어 기제 #102] Hot/Cold 재시작 구분 및 런타임 변경 제한.
    """
    
    # [방어 기제 #111] 시스템 재시작 없이 변경 불가능한 설정 (Cold Restart Keys)
    COLD_RESTART_KEYS: Set[str] = {
        "queue_size", 
        "broker_adapter_type", 
        "event_bus_depth", 
        "memory_zeroization_mode"
    }

    # [방어 기제 #111] 런타임 Hot Reload가 허용되는 설정
    HOT_RELOAD_KEYS: Set[str] = {
        "risk_weight_latency_alert", 
        "gamma_scalping_band_min", 
        "gamma_scalping_band_max",
        "composite_risk_threshold"
    }

    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """[①사유]: 설정파일의 정합성 로딩. [②위험성]: 파싱 에러 시 시스템 즉시 Halt."""
        if not os.path.exists(self.config_path):
            logger.critical(f"Config file missing at {self.config_path}")
            raise FileNotFoundError("System cannot boot without configuration.")
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self._validate_schema()
            logger.info("Configuration loaded and validated successfully.")
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON format in config: {e}")
            raise

    def _validate_schema(self) -> None:
        """[①사유]: 명세서 필수 설정값 존재 여부 검증."""
        required_keys = ["mdd_shutdown_pct", "max_kelly_fraction"]
        for key in required_keys:
            if key not in self.config:
                raise KeyError(f"Missing mandatory configuration key: {key}")

    def update_config(self, key: str, value: Any) -> bool:
        """
        [①사유]: 런타임 설정 변경 수행.
        [②위험성]: Cold Restart 키 변경 시도 시 차단 및 시스템 경고.
        """
        if key in self.COLD_RESTART_KEYS:
            logger.warning(f"SECURITY BLOCK: '{key}' change requires COLD RESTART. Change ignored.")
            return False
            
        if key in self.HOT_RELOAD_KEYS:
            self.config[key] = value
            logger.info(f"Hot Reload applied: {key} -> {value}")
            return True
            
        logger.error(f"Configuration key '{key}' is not registered for update.")
        return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
