"""Utility functionality used within bazkek."""

from typing import Awaitable, NamedTuple, TypeVar

import asyncio


T = TypeVar('T')


class Error(NamedTuple):
    """Representation of an error that can arise in bazmek."""

    message: str


Result = T | Error


def sync(awaitable: Awaitable[T]) -> T:
    """Synchronosly wait for the result."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(awaitable)
