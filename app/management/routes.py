from fastapi import APIRouter
from .models import NodeStatus
from app.chain.node_registry import node_registry

management_router = APIRouter()

@management_router.get('/ping')
def ping():
    return "pong"

@management_router.get('/v1/status')
def status():
    node_status: NodeStatus = {
        'id': node_registry.node_id,
        'supported_models': ['mistral-7b'],
    }
    return node_status
