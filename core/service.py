from datetime import datetime
from enum import Enum
from typing import NamedTuple


class Status(Enum):
    OK = 'OK'
    DOWN = 'DOWN'
    UNKNOWN = 'UNKNOWN'


class Service(NamedTuple):
    name: str
    last_check: datetime
    last_status: Status
    heartbeat_required: bool
    last_heartbeat: datetime

