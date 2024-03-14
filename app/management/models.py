from dataclasses import dataclass
from typing import List

@dataclass
class NodeStatus:
    id: int
    supported_models: List[str]
    has_capacity: bool = True
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
