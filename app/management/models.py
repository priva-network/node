from dataclasses import dataclass
from typing import List

@dataclass
class NodeStatus:
    id: int
    has_capacity: bool = True
    costs_per_1000_tokens: dict = None
    models_supported: List[str] = None
    models_running: List[str] = None
    models_downloaded: List[str] = None
    # TODO: Add more fields here

@dataclass
class SessionUsage:
    tokens: int
    wei: int
    usd: float

@dataclass
class SessionState:
    id: int
    tokens_used: int

@dataclass
class SessionReceipt:
    session_id: int
    usage: SessionUsage
    signature: str
