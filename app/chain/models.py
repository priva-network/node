from dataclasses import dataclass

@dataclass
class SessionDetails:
    id: int
    start_time: int
    compute_cost_limit: int
    user: str
    node_id: int
    is_active: bool
    amount_paid: int
