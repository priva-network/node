from typing import Tuple, Union
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer,
    PreTrainedTokenizer, PreTrainedTokenizerFast
)
from .models import CompletionRequest, ChatCompletionRequest
from threading import Thread
import logging
from app.models.storage import model_storage
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

current_model_name = None
tokenizer = None
model = None

def get_supported_models():
    return model_storage.get_supported_models()

async def is_model_loaded(model_name: str) -> bool:
    return model_name == current_model_name

async def is_model_downloaded(model_name: str) -> bool:
    return await model_storage.is_model_downloaded(model_name)

async def setup_model_if_not_running(model_name: str):
    global tokenizer, model, current_model_name

    model_path = await model_storage.get_model_dir(model_name)

    try:
        if model is None:
            logging.debug(f"No model loaded, loading {model_name} from {model_path}...")
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            if tokenizer.pad_token is None:
                if tokenizer.eos_token:
                    tokenizer.pad_token = tokenizer.eos_token
                else:
                    tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                    # Make sure to resize model embeddings if you're adding a new token
                    model.resize_token_embeddings(len(tokenizer))
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                pad_token_id=0
            )
            current_model_name = model_name
            model.to(device)
            logging.debug(f"Model loaded: {model_name}")
        elif model_name != current_model_name:
            logging.debug(f"Model changed, loading {model_name} from {model_path}...")
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            if tokenizer.pad_token is None:
                if tokenizer.eos_token:
                    tokenizer.pad_token = tokenizer.eos_token
                else:
                    tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                    # Make sure to resize model embeddings if you're adding a new token
                    model.resize_token_embeddings(len(tokenizer))
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                pad_token_id=0
            )
            current_model_name = model_name
            model.to(device)
            logging.debug(f"Model loaded: {model_name}")
        else:
            logging.debug(f"Model already loaded: {model_name}")
    except Exception as e:
        logging.error(f"Failed to load model: {e}", exc_info=True)
        raise e

def parse_prompt_format(prompt) -> Tuple[bool, list]:
    # get the prompt, openai supports the following
    # "a string, array of strings, array of tokens, or array of token arrays."
    prompt_is_tokens = False
    prompts = [prompt]  # case 1: a string
    if isinstance(prompt, list):
        if len(prompt) == 0:
            raise ValueError("please provide at least one prompt")
        elif isinstance(prompt[0], str):
            prompt_is_tokens = False
            prompts = prompt  # case 2: array of strings
        elif isinstance(prompt[0], int):
            prompt_is_tokens = True
            prompts = [prompt]  # case 3: array of tokens
        elif isinstance(prompt[0], list) and isinstance(prompt[0][0], int):
            prompt_is_tokens = True
            prompts = prompt  # case 4: array of token arrays
        else:
            raise ValueError("prompt must be a string, array of strings, "
                             "array of tokens, or array of token arrays")
    return prompt_is_tokens, prompts

def create_completion(request: CompletionRequest) -> (
        Union[str, TextIteratorStreamer],
        Union[PreTrainedTokenizer, PreTrainedTokenizerFast, None],
        int, Union[int, None]
    ):
    generate_params = request.to_generate_params()
    _, prompts = parse_prompt_format(request.prompt)

    inputs = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True).to(device)
    num_input_tokens = inputs.input_ids.shape[1]

    if request.stream:
        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=(not request.echo),
        )

        generation_kwargs = dict(inputs, streamer=streamer, **generate_params)
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        return streamer, tokenizer, num_input_tokens, None
    
    outputs = model.generate(**inputs, **generate_params)
    num_output_tokens = outputs.shape[1] - num_input_tokens
    outputs_to_decode = outputs[0]
    if not request.echo:
        outputs_to_decode = outputs[0, num_input_tokens:]
    response_text = tokenizer.decode(outputs_to_decode, skip_special_tokens=True)

    return response_text, tokenizer, num_input_tokens, num_output_tokens

def create_chat_completion(request: ChatCompletionRequest) -> (
        Union[str, TextIteratorStreamer],
        Union[PreTrainedTokenizer, PreTrainedTokenizerFast, None],
        int, Union[int, None]
    ):
    generate_params = request.to_generate_params()
    
    tokenized_chat = tokenizer.apply_chat_template(request.messages, tokenize=True, add_generation_prompt=True, return_tensors="pt").to(device)
    num_input_tokens = tokenized_chat.shape[1]

    if request.stream:
        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=True
        )

        generation_kwargs = dict(streamer=streamer, **generate_params)
        thread = Thread(target=model.generate, args=(tokenized_chat,), kwargs=generation_kwargs)
        thread.start()

        return streamer, tokenizer, num_input_tokens, None
    
    outputs = model.generate(tokenized_chat, **generate_params)
    num_output_tokens = outputs.shape[1] - num_input_tokens
    outputs_to_decode = outputs[0, num_input_tokens:]
    response_text = tokenizer.decode(outputs_to_decode, skip_special_tokens=True)

    return response_text, tokenizer, num_input_tokens, num_output_tokens
