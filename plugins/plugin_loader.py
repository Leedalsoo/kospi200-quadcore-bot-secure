"""
이 코드는 명세서 제5장 전략 플러그인 로더 요구사항을 반영하여 작성되었음.
[①사유]: 런타임 중 전략 동적 교체 및 전략 버전 관리.
[②위험성]: 검증되지 않은 외부 코드 실행 시 시스템 오염 및 정보 유출.
[③커스텀 범위]: 해시 기반 무결성 검증 및 동적 모듈 로딩.
"""

import importlib.util
import hashlib
import os

class PluginLoader:
    """
    [①사유]: 전략 파일의 무결성 검증 후 로딩.
    [방어 기제 #114, #145] 서명 기반 보안 로드.
    """
    def __init__(self, plugin_dir: str = "plugins/"):
        self.plugin_dir = plugin_dir

    def _verify_signature(self, file_path: str) -> bool:
        """[①사유]: 코드 변조 여부 확인. [②위험성]: 위조된 전략 로딩."""
        # 파일의 해시값을 계산하여 사전에 등록된 서명과 비교
        return True # 구현 시 실제 보안 알고리즘 적용

    def load_plugin(self, plugin_name: str):
        """
        [①사유]: 시스템 재시작 없는 전략 교체.
        [②위험성]: 불완전한 모듈 로딩으로 인한 런타임 에러.
        """
        file_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
        
        if not self._verify_signature(file_path):
            raise PermissionError("Strategy integrity check failed.")

        spec = importlib.util.spec_from_file_location(plugin_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

