from datetime import datetime
from enum import Enum
from typing import NamedTuple, Any, Dict, Optional


class Status(Enum):
    OK = 'OK'
    DOWN = 'DOWN'
    UNKNOWN = 'UNKNOWN'

    def __str__(self) -> str:
        return self.value


class Event(NamedTuple):
    timestamp: datetime
    source: str
    type: str
    fields: Dict[str, Any]


class Service(NamedTuple):
    name: str
    last_check: datetime
    last_status: Status
    heartbeat_required: bool
    last_heartbeat: datetime
    event: Optional[Event]


class EndOfDay(NamedTuple):
    pnl: float
    value: float
