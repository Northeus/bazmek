from typing import Awaitable, NamedTuple, TypeVar

import asyncio


T = TypeVar('T')


class Error(NamedTuple):
    message: str


Result = T | Error


def sync(awaitable: Awaitable[T]) -> T:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(awaitable)

