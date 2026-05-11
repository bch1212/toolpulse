"""@monitor must NEVER crash or block the caller. These tests prove that."""

import asyncio
import os

import pytest

# Disable network reporting for the duration of tests
os.environ.pop("TOOLPULSE_API_KEY", None)

from toolpulse import monitor, configure


def test_sync_function_returns_unchanged():
    @monitor(tool_name="adder")
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_sync_function_exception_propagates():
    @monitor(tool_name="boom")
    def boom():
        raise ValueError("expected")

    with pytest.raises(ValueError, match="expected"):
        boom()


@pytest.mark.asyncio
async def test_async_function_returns_unchanged():
    @monitor(tool_name="async_add")
    async def add(a, b):
        await asyncio.sleep(0)
        return a + b

    result = await add(2, 3)
    assert result == 5


@pytest.mark.asyncio
async def test_async_function_exception_propagates():
    @monitor(tool_name="async_boom")
    async def boom():
        raise RuntimeError("expected")

    with pytest.raises(RuntimeError, match="expected"):
        await boom()


def test_decorator_never_crashes_with_unserializable_response():
    """If the response can't be fingerprinted, the call still succeeds."""

    class Unserializable:
        def __repr__(self):
            return "<weird>"

    @monitor(tool_name="weird")
    def weird():
        return Unserializable()

    result = weird()
    assert isinstance(result, Unserializable)


def test_decorator_works_when_api_key_unset():
    """No API key = monitoring is a no-op, but caller behavior is unchanged."""
    configure(api_key=None)

    @monitor(tool_name="silent")
    def echo(x):
        return x

    assert echo(42) == 42
