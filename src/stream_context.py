"""Context for streaming reasoning from main and sub-agents to the UI."""
import contextvars
from typing import Callable, Awaitable, Optional

# Callback: (agent_name: str, chunk: str) -> Awaitable[None]
StreamSink = Callable[[str, str], Awaitable[None]]
_stream_sink: contextvars.ContextVar[Optional[StreamSink]] = contextvars.ContextVar(
    "stream_sink", default=None
)


def set_stream_sink(sink: Optional[StreamSink]) -> contextvars.Token:
    """Set the stream sink for the current context. Returns a token to reset."""
    return _stream_sink.set(sink)


def reset_stream_sink(token: contextvars.Token) -> None:
    """Reset the stream sink using the token from set_stream_sink."""
    _stream_sink.reset(token)


def get_stream_sink() -> Optional[StreamSink]:
    """Get the current stream sink, if any."""
    return _stream_sink.get()
