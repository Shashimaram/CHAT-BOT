import json
import re
import uuid
import logging

logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)

from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.superviser import main_agent
from src.stream_context import set_stream_sink, reset_stream_sink
from langchain_core.messages import AIMessageChunk, ToolMessage
import os

app = FastAPI()

# Serve saved chart images at /charts/<filename>
# Use absolute path so it works regardless of cwd
_CHARTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_charts")
os.makedirs(_CHARTS_DIR, exist_ok=True)
app.mount("/charts", StaticFiles(directory=_CHARTS_DIR), name="charts")

# Regex to detect chart file paths returned by visualization tools
_CHART_PATH_RE = re.compile(r"generated_charts[\\/][^\s\"'<>]+\.png")


async def _send_reasoning(websocket: WebSocket, agent: str, text: str) -> None:
    await websocket.send_text(
        json.dumps({"type": "reasoning", "data": text, "agent": agent})
    )


def _extract_reasoning_and_text(chunk: AIMessageChunk) -> tuple[str, str]:
    """
    Extract (reasoning_text, output_text) from a model chunk.

    Bedrock/langchain chunks can be plain text or structured blocks like:
    [{"type":"reasoning_content","reasoning_content":{"text":"..."}},
     {"type":"text","text":"..."}]
    """
    reasoning_parts: list[str] = []
    output_parts: list[str] = []
    content = getattr(chunk, "content", None)

    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "reasoning_content":
                rc = block.get("reasoning_content")
                if isinstance(rc, dict):
                    txt = rc.get("text")
                    if isinstance(txt, str) and txt:
                        reasoning_parts.append(txt)
            elif block_type == "text":
                txt = block.get("text")
                if isinstance(txt, str) and txt:
                    output_parts.append(txt)

    # Fallback: unstructured text chunks
    if not output_parts and isinstance(getattr(chunk, "text", None), str):
        txt = chunk.text
        if txt:
            output_parts.append(txt)

    return "".join(reasoning_parts), "".join(output_parts)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Each WebSocket connection gets its own thread — the checkpointer
    # accumulates the full message history automatically.
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        while True:
            data = await websocket.receive_text()
            try:
                full_output = []  # accumulate all output text

                ctx_token = set_stream_sink(
                    lambda a, t: _send_reasoning(websocket, a, t)
                )
                try:
                    async for event in main_agent.astream(
                        {"messages": [{"role": "user", "content": data}]},
                        config=config,
                        stream_mode="messages",
                    ):
                        if isinstance(event, tuple) and len(event) == 2:
                            token, _ = event
                        else:
                            token = event

                        # Stream AI text / reasoning tokens
                        if isinstance(token, AIMessageChunk):
                            reasoning_text, output_text = _extract_reasoning_and_text(token)
                            if reasoning_text:
                                await _send_reasoning(websocket, "main_agent", reasoning_text)
                            if output_text:
                                full_output.append(output_text)
                                await websocket.send_text(
                                    json.dumps({"type": "chunk", "data": output_text})
                                )

                        # Catch tool results that contain chart file paths
                        elif isinstance(token, ToolMessage):
                            content = token.content if isinstance(token.content, str) else str(token.content)
                            chart_paths = _CHART_PATH_RE.findall(content)
                            for path in chart_paths:
                                filename = os.path.basename(path)
                                chart_url = f"/charts/{filename}"
                                await websocket.send_text(
                                    json.dumps({"type": "chart", "data": chart_url})
                                )
                finally:
                    reset_stream_sink(ctx_token)

                await websocket.send_text(json.dumps({"type": "done"}))
            except Exception as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": str(e)})
                )
    except WebSocketDisconnect:
        pass


@app.get("/")
async def get_index():
    return HTMLResponse(content=open("UI/index.html").read(), media_type="text/html")
