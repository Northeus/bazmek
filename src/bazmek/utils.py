"""Utility functionality used within bazkek."""

from pathlib import Path
from PIL import Image
from typing import Awaitable, NamedTuple, TypeVar

import asyncio
import base64
import io


T = TypeVar('T')


class Error(NamedTuple):
    """Representation of an error that can arise in bazmek."""

    message: str


Result = T | Error


def sync(awaitable: Awaitable[T]) -> T:
    """Synchronosly wait for the result."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(awaitable)


def img_to_base64(image: Path, *, new_size: tuple[int, int] | None) -> str:
    """Encode image to base64 and optionally also resize it."""
    img = Image.open(image)
    img = img.resize(new_size) if new_size else img
    buffer = io.BytesIO()
    img.save(buffer, format='png')
    return base64.b64encode(buffer.getvalue()).decode()
