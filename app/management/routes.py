from fastapi import APIRouter, Request
from .models import NodeStatus
from app.chain.wallet import wallet
from app.chain.node_registry import node_registry
from .utils import get_session_tokens_used
from app.cost import cost_calculator
from app.models.storage import model_storage

management_router = APIRouter()

@management_router.get('/ping')
def ping():
    return "pong"

@management_router.get('/v1/status')
def status():
    node_status: NodeStatus = {
        'node_id': node_registry.node_id,
        'supported_models': model_storage.get_supported_models(),
        'has_capacity': True,
        'costs_per_1000_tokens': cost_calculator.get_full_cost_map(),
    }
    return node_status

@management_router.get('/v1/receipt')
def receipt(request: Request):
    session_id = request.query_params.get('session_id')
    if session_id is None:
        return "session_id is required", 400
    
    # convert session_id to int
    try:
        session_id = int(session_id)
    except ValueError:
        return "session_id must be an integer", 400
    
    tokens_used = get_session_tokens_used(session_id)
    amount_paid_usd = cost_calculator.calculate_cost(tokens_used, currency="USD")
    amount_paid_wei = cost_calculator.convert_to_wei(amount_paid_usd)

    signature, _ = wallet.sign_close_message(session_id, amount_paid_wei)

    return {
        'session_id': session_id,
        'usage': {
            'tokens': tokens_used,
            'wei': amount_paid_wei,
            'usd': amount_paid_usd,
        },
        'signature': signature,
    }
