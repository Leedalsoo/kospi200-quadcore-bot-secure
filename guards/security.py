"""
[①사유]: 시스템 보안 및 민감 데이터 유출 방지.
[②방어 기제 #73, #121, #173]: 로그 마스킹 및 메모리 안전성 관리.
"""

import logging
import re

class SecurityGuard:
    def __init__(self):
        self.logger = logging.getLogger("SecurityGuard")
        # 민감 정보 패턴 (예: 계좌번호, API 키 패턴)
        self.sensitive_pattern = re.compile(r"(account_number|api_key|secret)[:\s]+[^\s,]+", re.IGNORECASE)

    def mask_sensitive_data(self, data: str) -> str:
        """[①사유]: 로그 내 민감 정보 마스킹."""
        return self.sensitive_pattern.sub(r"\1: *****", data)

    def secure_memory_wipe(self, sensitive_data: bytearray):
        """[①사유]: 메모리 내 민감 정보 제로화 (Zeroing)."""
        # [방어 기제 #173]: 메모리 데이터 파괴
        for i in range(len(sensitive_data)):
            sensitive_data[i] = 0
        self.logger.info("Sensitive memory buffer wiped successfully.")
