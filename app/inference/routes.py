from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from .models import CompletionRequest, ChatCompletionRequest
from .services import (
    setup_model_if_not_running,
    create_completion,
    create_chat_completion,
    is_model_downloaded,
    is_model_loaded,
    get_supported_models
)
from app.management.utils import increment_session_tokens_used, get_session_tokens_used
from app.chain.utils import get_session_details
from app.cost import cost_calculator
import json
import time
import uuid

inference_router = APIRouter()

def _is_valid_session(session_id, request_max_tokens=None):
    session = get_session_details(session_id)
    if session is None:
        return False
    if not session.is_active:
        return False

    tokens_used = get_session_tokens_used(session_id)
    if tokens_used is None:
        tokens_used = 0

    cost_in_wei = cost_calculator.calculate_cost(tokens_used, currency="ETH_WEI")
    if cost_in_wei is None:
        return False
    
    if cost_in_wei > session.compute_cost_limit:
        return False

    request_max_cost_in_wei = cost_calculator.calculate_cost(request_max_tokens, currency="ETH_WEI")
    if request_max_cost_in_wei is not None and cost_in_wei + request_max_cost_in_wei > session.compute_cost_limit:
        return False

    return True

@inference_router.post('/v1/completions')
async def completions(request: CompletionRequest, raw_request: Request):
    session_id = raw_request.query_params.get('session_id')
    if session_id is None:
        return Response(status_code=400, content='{"error": "session_id is required"}')
    # convert session_id to int
    try:
        session_id = int(session_id)
    except ValueError:
        return "session_id must be an integer", 400

    model = request.model.lower()
    if model is None:
        return Response(status_code=400, content='{"error": "model is required"}')
    if model not in get_supported_models():
        return Response(status_code=400, content='{"error": "model is not supported"}')
    
    if not _is_valid_session(session_id):
        return Response(status_code=400, content='{"error": "session_id is invalid"}')
    
    await setup_model_if_not_running(model)

    result, tokenizer, num_input_tokens, num_output_tokens = create_completion(request)

    id = f"cmpl-{uuid.uuid4()}"
    created_time = int(time.time())

    response_template = {
        "choices": [],
        "created": created_time,
        "id": id,
        "model": model,
    }

    if not request.stream:
        if not isinstance(result, str):
            return Response(status_code=500, content='{"error": "Internal server error"}')
        
        increment_session_tokens_used(session_id, num_input_tokens + num_output_tokens)

        response = {
            **response_template,
            "object": "text_completion",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "text": result
                }
            ],
            "usage": {
                "prompt_tokens": num_input_tokens,
                "completion_tokens": num_output_tokens,
                "total_tokens": num_input_tokens + num_output_tokens if num_output_tokens is not None else None
            }
        }
        return Response(content=json.dumps(response), media_type="application/json")
    
    streamer = result

    def stream_response():
        num_output_tokens = 0

        for new_text in streamer:
            new_tokens = tokenizer.encode(new_text, add_special_tokens=False)
            num_output_tokens += len(new_tokens)

            response = {
                **response_template,
                "object": "text_completion.chunk",
                "choices": [
                    {
                        "finish_reason": None,
                        "index": 0,
                        "logprobs": None,
                        "text": new_text
                    }
                ]
            }
            yield json.dumps(response) + "\n"

        if request.echo:
            # if echoing, it outputs both input and output tokens,
            # so we need to subtract the input tokens from the total
            num_output_tokens -= num_input_tokens
        increment_session_tokens_used(session_id, num_input_tokens + num_output_tokens)

        final_response = {
            **response_template,
            "object": "text_completion.chunk",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "text": ""
                }
            ]
        }
        yield json.dumps(final_response) + "\n"
        yield "[DONE]\n"

    return StreamingResponse(stream_response(), media_type="text/plain", headers={"Transfer-Encoding": "chunked"})

@inference_router.post('/v1/chat/completions')
async def completions_chat(request: ChatCompletionRequest, raw_request: Request):
    session_id = raw_request.query_params.get('session_id')
    if session_id is None:
        return Response(status_code=400, content='{"error": "session_id is required"}')
    # convert session_id to int
    try:
        session_id = int(session_id)
    except ValueError:
        return "session_id must be an integer", 400

    model = request.model.lower()
    if model is None:
        return Response(status_code=400, content='{"error": "model is required"}')
    if model not in get_supported_models():
        return Response(status_code=400, content='{"error": "model is not supported"}')

    if not _is_valid_session(session_id):
        return Response(status_code=400, content='{"error": "session_id is invalid"}')
    
    await setup_model_if_not_running(model)
    
    result, tokenizer, num_input_tokens, num_output_tokens = create_chat_completion(request)

    id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())

    response_template = {
        "choices": [],
        "created": created_time,
        "id": id,
        "model": model,
    }

    if not request.stream:
        if not isinstance(result, str):
            return Response(status_code=500, content='{"error": "Internal server error"}')
        
        increment_session_tokens_used(session_id, num_input_tokens + num_output_tokens)

        response = {
            **response_template,
            "object": "chat.completion",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": result
                    },
                    "logprobs": None,
                    "finish_reason": "stop",
                    "index": 0
                }
            ],
            "usage": {
                "prompt_tokens": num_input_tokens,
                "completion_tokens": num_output_tokens,
                "total_tokens": num_input_tokens + num_output_tokens if num_output_tokens is not None else None
            }
        }
        return Response(content=json.dumps(response), media_type="application/json")
    
    # otherwise, we are streaming
    streamer = result

    def stream_response():
        num_output_tokens = 0

        for new_text in streamer:
            new_tokens = tokenizer.encode(new_text, add_special_tokens=False)
            num_output_tokens += len(new_tokens)

            response = {
                **response_template,
                "object": "chat.completion.chunk",
                "choices": [
                    {
                        "delta": {
                            "content": new_text
                        },
                        "finish_reason": None,
                        "index": 0,
                        "logprobs": None
                    }
                ]
            }
            yield json.dumps(response) + "\n"

        increment_session_tokens_used(session_id, num_input_tokens + num_output_tokens)

        final_response = {
            **response_template,
            "object": "chat.completion.chunk",
            "choices": [
                {
                    "delta": {},
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None
                }
            ]
        }
        yield json.dumps(final_response) + "\n"
        yield "[DONE]\n"

    return StreamingResponse(stream_response(), media_type="text/plain", headers={"Transfer-Encoding": "chunked"})
