from flask import Blueprint, request, jsonify
from .models import NodeStatus
from app.chain.node_registry import node_registry

management_bp = Blueprint('management', __name__)

@management_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify('pong')

@management_bp.route('/v1/status', methods=['GET'])
def status():
    node_status: NodeStatus = {
        'id': node_registry.node_id,
        'supported_models': ['mistral-7b'],
    }
    return jsonify(node_status)
