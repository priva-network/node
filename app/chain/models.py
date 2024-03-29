from dataclasses import dataclass

@dataclass
class NodeDetails:
    id: int
    ip_address: str
    owner: str

@dataclass
class SessionDetails:
    id: int
    start_time: int
    compute_cost_limit: int
    user: str
    node_id: int
    is_active: bool
    amount_paid: int

@dataclass
class ModelDetails:
    name: str
    ipfs_hash: str
