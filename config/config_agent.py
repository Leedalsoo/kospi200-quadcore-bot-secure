"""
[①사유]: 설정 정보 중앙 집중화 및 무결성 검증.
[②방어 기제 #7-4]: 하드웨어 한도와 런타임 설정을 분리하여 물리적 보호.
"""
import json
import yaml
import logging

class ConfigAgent:
    def __init__(self, hard_limits_path="config/hard_limits.yaml", settings_path="config/settings.json"):
        self.hard_limits = self._load_yaml(hard_limits_path)
        self.settings = self._load_json(settings_path)
        self.validate()

    def _load_yaml(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _load_json(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def validate(self):
        """[방어 기제 #35] 리스크 설정이 하드 한도를 초과하는지 검증."""
        if self.settings['risk_thresholds']['mdd_shutdown_pct'] > self.hard_limits['max_mdd']:
            raise ValueError("CRITICAL: Risk threshold exceeds hard limits!")
        logging.info("ConfigAgent: 무결성 검증 완료.")

    def get(self, key, default=None):
        return self.settings.get(key, default)

