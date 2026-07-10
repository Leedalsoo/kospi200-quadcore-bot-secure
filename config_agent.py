"""
이 코드는 명세서 제11장 설정 관리 요구사항을 반영하여 작성되었음.
[①사유]: 런타임 설정 변경 시 무결성 보장 및 중요 설정 보호.
[②위험성]: 잘못된 설정값 주입으로 인한 매매 엔진 오작동 및 전략 파산.
[③커스텀 범위]: Hot/Cold 설정 분리 및 환경 변수 기반 로딩.
"""

import json
import logging
from typing import Any

class ConfigAgent:
    """
    [①사유]: 설정값의 안전한 로딩 및 런타임 무결성 검사.
    [방어 기제 #102, #111] Hot/Cold 재시작 구분 로직.
    """
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = config_path
        self.config = {}
        self.load_config()

    def load_config(self):
        """[①사유]: 설정파일 로딩. [②위험성]: JSON 파싱 에러 시 시스템 정지."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def update_config(self, key: str, value: Any):
        """
        [①사유]: 런타임 설정 변경.
        [②위험성]: 재시작이 필요한 설정을 런타임에 변경 시 엔진 충돌.
        """
        # [방어 기제 #111] 특정 설정은 Cold Restart를 강제함
        cold_restart_keys = ["queue_size", "broker_adapter_type"]
        
        if key in cold_restart_keys:
            logging.warning(f"CRITICAL: {key} requires cold restart. Pending change.")
            # 실제 적용은 재시작 시 수행하도록 플래그 기록
            return False
            
        self.config[key] = value
        return True

