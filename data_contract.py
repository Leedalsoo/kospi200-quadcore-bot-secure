"""
시스템 표준 데이터 모델 정의서
[①사유]: 에이전트 간 통신 시 타입 안정성 및 데이터 구조 통일.
[②위험성]: 데이터 구조 불일치 시 모듈 간 통신 장애 및 런타임 타입 에러 발생.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    CREATED = "CREATED"; PENDING = "PENDING"; SENT = "SENT"
    PARTIAL = "PARTIAL"; FILLED = "FILLED"; CANCELLED = "CANCELLED"; REJECTED = "REJECTED"

@dataclass(frozen=True)
class OrderRequest:
    """[①사유]: 주문 요청 데이터 규격. [방어 기제 #1] 데이터 불변성 보장."""
    client_order_id: str
    symbol: str
    qty: int
    price: float
    timestamp: datetime = datetime.now()

@dataclass(frozen=True)
class ExecutionReport:
    """[①사유]: 거래소 체결 결과 표준 규격."""
    order_id: str
    status: OrderStatus
    filled_qty: int
    filled_price: float
    timestamp: datetime

