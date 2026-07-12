"""
이 코드는  명세서 제2장의 요구사항을 반영하여 작성되었음.
[①사유]: Rust-Python 간 Zero-copy 메모리 호환 및 타입 안정성 확보.
[②위험성]: 타입 불일치 시 시스템 정지 및 OMS FSM 오류 발생.
[③커스텀 범위]: 본 시스템의 7대 핵심 데이터 컨트랙트 규격.
[방어 기제 매핑]: #112, #115, #134, #148, #154, #184, #200
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import List
from uuid import UUID

@dataclass(slots=True)
class MarketTick:
    """[①사유]: 시장 데이터 정형화. [②위험성]: 데이터 누락 시 오판. [③커스텀 범위]: 공통."""
    instrument_code: str = field(metadata={"description": "종목 코드"})
    timestamp: datetime = field(metadata={"description": "거래소 시각 KST"})
    last_price: float = field(metadata={"description": "최종 체결가(float64)"})
    volume: int = field(metadata={"description": "체결 수량(int64)"})
    bid_prices: List[float] = field(metadata={"description": "매수 호가 리스트(1~10)"})
    ask_prices: List[float] = field(metadata={"description": "매도 호가 리스트(1~10)"})
    bid_qtys: List[int] = field(metadata={"description": "매수 잔량 리스트(1~10)"})
    ask_qtys: List[int] = field(metadata={"description": "매도 잔량 리스트(1~10)"})

@dataclass(slots=True)
class InstrumentProfile:
    """[①사유]: 종목 제약 관리. [②위험성]: 규격 오인 시 주문 실패."""
    instrument_code: str
    strike_price: float
    tick_size_rule: float
    multiplier: int = 250000
    expiry_date: date = field(metadata={"description": "만기일"})
    is_underlying: bool = field(metadata={"description": "기초자산 여부"})

@dataclass(slots=True)
class OrderRequest:
    """[①사유]: 주문 무결성. [②위험성]: 파라미터 오염 시 파산. [③커스텀 범위]: LIMIT 고정."""
    decision_id: UUID
    client_order_id: UUID
    trace_id: str
    span_id: str
    instrument_code: str
    order_type: str = field(default="LIMIT", metadata={"description": "LIMIT 고정"})
    time_in_force: str = field(metadata={"description": "IOC/FOK"})
    side: str = field(metadata={"description": "BUY/SELL"})
    price: Decimal = field(metadata={"description": "주문 가격(Decimal)"})
    qty: int = field(metadata={"description": "주문 수량(int64)"})

@dataclass(slots=True)
class ExecutionReport:
    """[①사유]: 체결 이력 추적. [②위험성]: 미체결 확인 누락 시 포지션 불일치."""
    client_order_id: UUID
    broker_order_id: str
    fill_id: str
    status: str = field(metadata={"description": "OMS FSM 14단계 상태"})
    filled_qty: int
    filled_price: Decimal
    remaining_qty: int
    timestamp: datetime
    broker_raw_response: dict

@dataclass(slots=True)
class Position:
    """[①사유]: 실시간 평가. [②위험성]: 평균단가 오산 시 PnL 왜곡."""
    instrument_code: str
    role: str = field(metadata={"description": "MAIN_SHORT 등 역할"})
    avg_price: Decimal = field(metadata={"description": "이동평균법 적용 단가"})
    qty: int
    realized_pnl: Decimal
    unrealized_pnl: Decimal = field(metadata={"description": "평가 PnL"})

@dataclass(slots=True)
class DecisionLog:
    """[①사유]: 의사결정 추적. [②위험성]: 사후 복기 불가 방지."""
    decision_id: UUID
    trace_id: str
    timestamp: datetime
    trigger_type: str
    regime_state: str
    composite_risk_score: float
    confidence_score: float
    execution_quality_score: float
    reason: str

@dataclass(slots=True)
class HardLimitsConfig:
    """[①사유]: 생존 하드 리밋. [②위험성]: 수정 시 시스템 파산."""
    mdd_shutdown_pct: float
    max_kelly_fraction: float
    fat_finger_theo_dev_pct: float
    fat_finger_ltp_dev_pct: float
    max_order_qty_per_trade: int
    max_daily_loss_amount: Decimal

