from flask import jsonify, Response, stream_with_context
from vllm.vllm.entrypoints.openai.serving_chat import OpenAIServingChat
from vllm.vllm.entrypoints.openai.serving_completion import OpenAIServingCompletion
from vllm.vllm import AsyncEngineArgs, AsyncLLMEngine
from vllm.vllm.entrypoints.openai.protocol import (
    ChatCompletionRequest, CompletionRequest,
    ErrorResponse
)

# Leverages functions in vllm submodule to handle requests.
# Basically copies the logic from vllm.vllm.entrypoints.openai.api_server
# but converts it into code compatible with Flask requests.

current_model = None
openai_serving_chat: OpenAIServingChat = None
openai_serving_completion: OpenAIServingCompletion = None

def setup_model_if_not_running(model: str):
    global current_model, openai_serving_chat, openai_serving_completion
    if current_model == model:
        return
    
    current_model = model

    engine_args = AsyncEngineArgs(model=model)
    engine = AsyncLLMEngine.from_engine_args(engine_args)

    openai_serving_chat = OpenAIServingChat(engine, served_model=model)
    openai_serving_completion = OpenAIServingCompletion(engine, served_model=model)

def create_chat_completion(request):
    if openai_serving_chat is None:
        raise ValueError("Model not initialized")

    try:
        # Parse the incoming JSON request into a ChatCompletionRequest instance
        chat_request_data = request.json
        chat_request = ChatCompletionRequest(**chat_request_data)
    except ValueError as e:
        # Handle parsing errors, e.g., missing fields or validation errors
        return jsonify({"error": str(e)}), 400

    # Assuming a synchronous version of create_chat_completion exists or has been adapted
    generator = openai_serving_chat.create_chat_completion(chat_request, request)

    if isinstance(generator, ErrorResponse):
        # Assuming ErrorResponse has a method `model_dump` for serialization
        return jsonify(generator.model_dump()), generator.code

    if chat_request.stream:
        def generate():
            for item in generator:
                # Assuming generator yields strings; adjust as needed
                yield item
        return Response(generate(), mimetype="text/event-stream")
    else:
        # Assuming generator has a method `model_dump` for serialization
        return jsonify(generator.model_dump())

def create_completion(request):
    if openai_serving_completion is None:
        raise ValueError("Model not initialized")

    try:
        # Parse the incoming JSON request into a CompletionRequest instance
        completion_request_data = request.json
        completion_request = CompletionRequest(**completion_request_data)
    except ValueError as e:
        # Handle parsing errors, e.g., missing fields or validation errors
        return jsonify({"error": str(e)}), 400

    # Assuming a synchronous version of create_completion exists or has been adapted
    generator = openai_serving_completion.create_completion(completion_request, request)

    if isinstance(generator, ErrorResponse):
        # Assuming ErrorResponse has a method `model_dump` for serialization
        return jsonify(generator.model_dump()), generator.code

    if completion_request.stream:
        def generate():
            for item in generator:
                # Assuming generator yields strings; adjust as needed
                yield item
        return Response(stream_with_context(generate()), mimetype="text/event-stream")
    else:
        # Assuming generator has a method `model_dump` for serialization
        return jsonify(generator.model_dump())