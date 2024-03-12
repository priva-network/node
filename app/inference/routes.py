from flask import Blueprint, request, jsonify
from .services import (
    setup_model_if_not_running,
    create_chat_completion,
    create_completion
)

inference_bp = Blueprint('inference', __name__)

@inference_bp.route('/v1/completions', methods=['POST'])
def completions():
    data = request.json
    model = data.get('model', None)
    if model is None:
        return jsonify({'error': 'model is required'}), 400
    
    setup_model_if_not_running(model)
    return create_completion(request)

@inference_bp.route('/v1/chat/completions', methods=['POST'])
def completions_chat():
    data = request.json
    model = data.get('model', None)
    if model is None:
        return jsonify({'error': 'model is required'}), 400
    
    setup_model_if_not_running(model)
    return create_chat_completion(request)
