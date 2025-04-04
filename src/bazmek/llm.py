"""
LLM hooks for Ollama API.

See classes `LLM` and `Config` for LLM set-up. Function `prompt` then send API
request to the LLM using either provided or default config.
"""

from __future__ import annotations

from bazmek import utils
from typing import (overload, Literal, NamedTuple, ReadOnly, TypedDict)

import aiohttp
import json


class LLM(NamedTuple):
    """
    LLM connection information.

    The `url` shold not end with '/'. A `model` parameter is the exact model
    name from Ollama.
    """

    Model = Literal['llama3.3', 'gemma3', 'phi4']

    url: str
    model: Model
    timeout_ms: int | None = None


class Message(NamedTuple):
    """
    LLM chat message with the information about the author.

    Use class methods `system`, `assistant`, and `user` for neater usage.
    """

    role: Literal['system', 'assistant', 'user']
    message: str

    @classmethod
    def system(cls, message: str) -> Message:
        """Create system message."""
        return Message(role='system', message=message)

    @classmethod
    def assistant(cls, message: str) -> Message:
        """Create assistant message."""
        return Message(role='assistant', message=message)

    @classmethod
    def user(cls, message: str) -> Message:
        """Create user message."""
        return Message(role='user', message=message)


class Config(TypedDict, total=False):
    """
    LLM parameters.

    You might want to increase the parameter `num_ctx` that represents the
    context window as it default value for model is usually small.

    For more information see:
    https://github.com/ollama/ollama/blob/main/docs/modelfile.md
    """

    mirostat: ReadOnly[int]
    mirostat_eta: ReadOnly[float]
    mirostat_tau: ReadOnly[float]
    num_ctx: ReadOnly[int]
    repeat_last_n: ReadOnly[int]
    repeat_penalty: ReadOnly[float]
    temperature: ReadOnly[float]
    seed: ReadOnly[int]
    stop: ReadOnly[list[str]]
    num_predict: ReadOnly[int]
    top_k: ReadOnly[int]
    top_p: ReadOnly[float]
    min_p: ReadOnly[float]


JSON = str | int | float | bool | list['JSON'] | dict[str, 'JSON']


@overload
async def prompt(llm: LLM,
                 messages: list[Message],
                 *,
                 config: Config = Config()
                 ) -> utils.Result[str]:
    ...


@overload
async def prompt(llm: LLM,
                 messages: list[Message],
                 *,
                 schema: JSON,
                 config: Config = Config(),
                 ) -> utils.Result[JSON]:
    ...


async def prompt(llm: LLM,
                 messages: list[Message],
                 *,
                 schema: JSON | None = None,
                 config: Config = Config()
                 ) -> utils.Result[str | JSON]:
    """
    Prompt LLM with messages to obtain a response.

    If a `scheme` is provided, then the result is an dictionary representation
    with the same form given by the scheme. Using `scheme` can hinder the LLM
    accuracy. Make sure, that answer does not preceed reasoning to mittigate
    halucinations generated by LLM. The format of scheme is:
    ```
    {
        "type": "object" | "array" | "bool" | "int" | "float" | "string",
        "description": "...",

        // For arrays:
        "items": { /* Format of another objects */ }

        // For objects:
        "properties": {
            "property_name": { /* Format of another objects */ },
        }
        "required": ["property_name"]

        // For enums (ommit "type"):
        "enum": [ /* Possible values */ ]
    }
    ```

    Additionally, LLM parameters can be configured using `config`.
    """
    data = {
        'model': llm.model,
        'messages': [x._asdict() for x in messages],
        'format': schema,
        'options': config,
        'stream': False
    }

    timeout_seconds = llm.timeout_ms and llm.timeout_ms / 1000
    async with (
            aiohttp.ClientSession(timeout=timeout_seconds) as session,
            session.post(llm.url + '/api/chat', json=data) as response):
        if not response.ok:
            return utils.Error(message=f'Invalid response: {str(response)}')

        body = await response.json()

    match schema:
        case None:
            return body['message']['content']
        case _:
            return json.loads(body['message']['content'])
