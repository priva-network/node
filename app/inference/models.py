from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator

import torch


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    max_tokens: Optional[int] = None
    seed: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = Field(default_factory=list)
    stream: Optional[bool] = False
    logprobs: Optional[bool] = False
    top_logprobs: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    # Additional parameters supported by vLLM
    best_of: Optional[int] = None
    top_k: Optional[int] = -1
    ignore_eos: Optional[bool] = False
    use_beam_search: Optional[bool] = False
    early_stopping: Optional[bool] = False
    stop_token_ids: Optional[List[int]] = Field(default_factory=list)
    skip_special_tokens: Optional[bool] = True
    spaces_between_special_tokens: Optional[bool] = True
    add_generation_prompt: Optional[bool] = True
    echo: Optional[bool] = False
    repetition_penalty: Optional[float] = 1.0
    min_p: Optional[float] = 0.0
    include_stop_str_in_output: Optional[bool] = False
    length_penalty: Optional[float] = 1.0
    guided_json: Optional[Union[str, dict, BaseModel]] = None
    guided_regex: Optional[str] = None
    guided_choice: Optional[List[str]] = None

    def to_sampling_params(self):
        if self.logprobs and not self.top_logprobs:
            raise ValueError("Top logprobs must be set when logprobs is.")

        logits_processors = None
        if self.logit_bias:

            def logit_bias_logits_processor(
                    token_ids: List[int],
                    logits: torch.Tensor) -> torch.Tensor:
                for token_id, bias in self.logit_bias.items():
                    # Clamp the bias between -100 and 100 per OpenAI API spec
                    bias = min(100, max(-100, bias))
                    logits[int(token_id)] += bias
                return logits

            logits_processors = [logit_bias_logits_processor]

        if torch.cuda.is_available():
            from vllm import SamplingParams
            return SamplingParams(
                n=self.n,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                repetition_penalty=self.repetition_penalty,
                temperature=self.temperature,
                top_p=self.top_p,
                min_p=self.min_p,
                seed=self.seed,
                stop=self.stop,
                stop_token_ids=self.stop_token_ids,
                max_tokens=self.max_tokens,
                logprobs=self.top_logprobs if self.logprobs else None,
                prompt_logprobs=self.top_logprobs if self.echo else None,
                best_of=self.best_of,
                top_k=self.top_k,
                ignore_eos=self.ignore_eos,
                use_beam_search=self.use_beam_search,
                early_stopping=self.early_stopping,
                skip_special_tokens=self.skip_special_tokens,
                spaces_between_special_tokens=self.spaces_between_special_tokens,
                include_stop_str_in_output=self.include_stop_str_in_output,
                length_penalty=self.length_penalty,
                logits_processors=logits_processors,
            )
        else:
            return {
                "n": self.n,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
                "repetition_penalty": self.repetition_penalty,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "min_p": self.min_p,
                "seed": self.seed,
                "stop": self.stop,
                "stop_token_ids": self.stop_token_ids,
                "max_tokens": self.max_tokens,
                "logprobs": self.top_logprobs if self.logprobs else None,
                "prompt_logprobs": self.top_logprobs if self.echo else None,
                "best_of": self.best_of,
                "top_k": self.top_k,
                "ignore_eos": self.ignore_eos,
                "use_beam_search": self.use_beam_search,
                "early_stopping": self.early_stopping,
                "skip_special_tokens": self.skip_special_tokens,
                "spaces_between_special_tokens": self.spaces_between_special_tokens,
                "include_stop_str_in_output": self.include_stop_str_in_output,
                "length_penalty": self.length_penalty,
                "logits_processors": logits_processors,
            }

    @model_validator(mode="before")
    @classmethod
    def check_guided_decoding_count(cls, data):
        guide_count = sum([
            "guided_json" in data and data["guided_json"] is not None,
            "guided_regex" in data and data["guided_regex"] is not None,
            "guided_choice" in data and data["guided_choice"] is not None
        ])
        if guide_count > 1:
            raise ValueError(
                "You can only use one kind of guided decoding "
                "('guided_json', 'guided_regex' or 'guided_choice').")
        return data

class CompletionRequest(BaseModel):
    model: str
    # a string, array of strings, array of tokens, or array of token arrays
    prompt: Union[List[int], List[List[int]], str, List[str]]
    suffix: Optional[str] = None
    max_tokens: Optional[int] = 16
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = Field(default_factory=list)
    seed: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    best_of: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    # Additional parameters supported by vLLM
    top_k: Optional[int] = -1
    ignore_eos: Optional[bool] = False
    use_beam_search: Optional[bool] = False
    early_stopping: Optional[bool] = False
    stop_token_ids: Optional[List[int]] = Field(default_factory=list)
    skip_special_tokens: Optional[bool] = True
    spaces_between_special_tokens: Optional[bool] = True
    repetition_penalty: Optional[float] = 1.0
    min_p: Optional[float] = 0.0
    include_stop_str_in_output: Optional[bool] = False
    length_penalty: Optional[float] = 1.0
    guided_json: Optional[Union[str, dict, BaseModel]] = None
    guided_regex: Optional[str] = None
    guided_choice: Optional[List[str]] = None

    def to_sampling_params(self):
        echo_without_generation = self.echo and self.max_tokens == 0

        logits_processors = None
        if self.logit_bias:

            def logit_bias_logits_processor(
                    token_ids: List[int],
                    logits: torch.Tensor) -> torch.Tensor:
                for token_id, bias in self.logit_bias.items():
                    # Clamp the bias between -100 and 100 per OpenAI API spec
                    bias = min(100, max(-100, bias))
                    logits[int(token_id)] += bias
                return logits

            logits_processors = [logit_bias_logits_processor]

        if torch.cuda.is_available():
            from vllm import SamplingParams
            return SamplingParams(
                n=self.n,
                best_of=self.best_of,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                repetition_penalty=self.repetition_penalty,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                min_p=self.min_p,
                seed=self.seed,
                stop=self.stop,
                stop_token_ids=self.stop_token_ids,
                ignore_eos=self.ignore_eos,
                max_tokens=self.max_tokens if not echo_without_generation else 1,
                logprobs=self.logprobs,
                use_beam_search=self.use_beam_search,
                early_stopping=self.early_stopping,
                prompt_logprobs=self.logprobs if self.echo else None,
                skip_special_tokens=self.skip_special_tokens,
                spaces_between_special_tokens=(self.spaces_between_special_tokens),
                include_stop_str_in_output=self.include_stop_str_in_output,
                length_penalty=self.length_penalty,
                logits_processors=logits_processors,
            )
        else:
            return {
                "n": self.n,
                "best_of": self.best_of,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
                "repetition_penalty": self.repetition_penalty,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "min_p": self.min_p,
                "seed": self.seed,
                "stop": self.stop,
                "stop_token_ids": self.stop_token_ids,
                "ignore_eos": self.ignore_eos,
                "max_tokens": self.max_tokens if not echo_without_generation else 1,
                "logprobs": self.logprobs,
                "use_beam_search": self.use_beam_search,
                "early_stopping": self.early_stopping,
                "prompt_logprobs": self.logprobs if self.echo else None,
                "skip_special_tokens": self.skip_special_tokens,
                "spaces_between_special_tokens": (self.spaces_between_special_tokens),
                "include_stop_str_in_output": self.include_stop_str_in_output,
                "length_penalty": self.length_penalty,
                "logits_processors": logits_processors,
            }

    @model_validator(mode="before")
    @classmethod
    def check_guided_decoding_count(cls, data):
        guide_count = sum([
            "guided_json" in data and data["guided_json"] is not None,
            "guided_regex" in data and data["guided_regex"] is not None,
            "guided_choice" in data and data["guided_choice"] is not None
        ])
        if guide_count > 1:
            raise ValueError(
                "You can only use one kind of guided decoding "
                "('guided_json', 'guided_regex' or 'guided_choice').")
        return data