from __future__ import annotations
from typing import Literal, NamedTuple, ReadOnly, TypedDict

import aiohttp
import utils


class LLM(NamedTuple):
    Model = Literal['llama3.3', 'gemma3', 'phi4']

    url: str
    model: Model
    timeout_ms: int | None = None


class Message(NamedTuple):
    role: Literal['system', 'assistant', 'user']
    message: str

    @classmethod
    def system(cls, message: str) -> Message:
        return Message(role='system', message=message)

    @classmethod
    def assistant(cls, message: str) -> Message:
        return Message(role='assistant', message=message)

    @classmethod
    def user(cls, message: str) -> Message:
        return Message(role='user', message=message)


# https://github.com/ollama/ollama/blob/main/docs/modelfile.md
class Config(TypedDict, total=False):
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


async def prompt(llm: LLM,
                 messages: list[Message],
                 *,
                 config: Config = Config(),
                 ) -> utils.Result[str]:
    assert len(messages) >= 1

    data = {
        'model': llm.model,
        'messages': list(map(lambda x: x._asdict(), messages)),
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
        return body['message']['content']
