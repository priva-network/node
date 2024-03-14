from typing import Tuple, Union
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer,
    PreTrainedTokenizer, PreTrainedTokenizerFast
)
from .models import CompletionRequest, ChatCompletionRequest
from threading import Thread
import logging

current_model_name = None
tokenizer = None
model = None

def setup_model_if_not_running(model_name: str):
    global tokenizer, model, current_model_name

    if model is None:
        logging.debug(f"No model loaded, loading {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        current_model_name = model_name
        logging.debug(f"Model loaded: {model_name}")
    elif model_name != current_model_name:
        logging.debug(f"Model changed, loading {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        current_model_name = model_name
        logging.debug(f"Model loaded: {model_name}")
    else:
        logging.debug(f"Model already loaded: {model_name}")


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

    inputs = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True)
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
    
    tokenized_chat = tokenizer.apply_chat_template(request.messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
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
