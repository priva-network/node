from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from .models import CompletionRequest, ChatCompletionRequest
from .services import (
    setup_model_if_not_running,
    create_completion,
)
import json

inference_router = APIRouter()

@inference_router.post('/v1/completions')
async def completions(request: CompletionRequest, raw_request: Request):
    model = request.model
    if model is None:
        return Response(status_code=400, content='{"error": "model is required"}')
    
    setup_model_if_not_running(model)

    generator = create_completion(request)

    async def stream_response():
        async for request_output in generator:
            prompt = request_output.prompt
            text_outputs = [
                prompt + output.text for output in request_output.outputs
            ]
            ret = {"text": text_outputs}
            yield (json.dumps(ret) + "\0").encode("utf-8")

    return StreamingResponse(stream_response(), media_type="text/plain", headers={"Transfer-Encoding": "chunked"})

@inference_router.post('/v1/chat/completions')
async def completions_chat(request: ChatCompletionRequest, raw_request: Request):
    model = request.model
    if model is None:
        return Response(status_code=400, content='{"error": "model is required"}')
    
    setup_model_if_not_running(model)
    return Response(status_code=200, content='{"success": true}')
