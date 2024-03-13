import torch
from typing import Tuple
from .models import CompletionRequest, ChatCompletionRequest

# TODO: I should switch over to AsyncLLMEngine from vllm
# Docs: https://docs.vllm.ai/en/latest/dev/engine/async_llm_engine.html

if torch.cuda.is_available():
    from vllm import LLM, SamplingParams

current_model = None
llm = None

class MockLLM:
    def generate(self, prompts, sampling_params, stream):
        for prompt in prompts:
            yield prompt + " generated\n"

def setup_model_if_not_running(model: str):
    global current_model
    global llm

    if current_model == model:
        return
    
    current_model = model
    if torch.cuda.is_available():
        llm = LLM(model=model)
    else:
        llm = MockLLM()


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

# How to stream response: https://github.com/vllm-project/vllm/issues/1946
def create_completion(request: CompletionRequest):

    sampling_params = request.to_sampling_params()
    _, prompts = parse_prompt_format(request.prompt)

    generator = llm.generate(
        prompts=prompts,
        sampling_params=sampling_params,
        stream=True,
    )

    return generator
