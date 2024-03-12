from dataclasses import dataclass
from typing import List

@dataclass
class NodeStatus:
    id: int
    supported_models: List[str]
    has_capacity: bool = True
    # TODO: Add more fields here
