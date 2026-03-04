import json
import logging
from contextlib import asynccontextmanager

logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)

from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from src.superviser import main_agent
from src.storage.session_handler import (
    init_chat_history,
    create_session,
    save_user_message,
    save_ai_message,
    load_session_messages,
    list_sessions,
    delete_session,
)
from langchain_core.messages import AIMessageChunk
import asyncio
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_chat_history()
    yield


app = FastAPI(lifespan=lifespan)

_CHARTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_charts")
os.makedirs(_CHARTS_DIR, exist_ok=True)
app.mount("/charts", StaticFiles(directory=_CHARTS_DIR), name="charts")


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

    if not output_parts and isinstance(getattr(chunk, "text", None), str):
        txt = chunk.text
        if txt:
            output_parts.append(txt)

    return "".join(reasoning_parts), "".join(output_parts)



@app.get("/sessions")
async def get_sessions():
    return JSONResponse(content=list_sessions())


@app.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    delete_session(session_id)
    return JSONResponse(content={"status": "deleted"})


# ── WebSocket with persistent chat history ──


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    session_id = websocket.query_params.get("session_id") or create_session()
    config = {"configurable": {"thread_id": session_id}}

    history = load_session_messages(session_id)
    await websocket.send_text(json.dumps({
        "type": "session_init",
        "session_id": session_id,
        "history": history,
    }))

    try:
        while True:
            data = await websocket.receive_text()
            save_user_message(session_id, data)

            try:
                ai_response_parts: list[str] = []

                async for stream_mode, chunk in main_agent.astream(
                    {"messages": [{"role": "user", "content": data}]},
                    config=config,
                    stream_mode=["messages", "custom"],
                ):
                    if stream_mode == "messages":
                        token, metadata = chunk

                        if isinstance(token, AIMessageChunk):
                            reasoning_text, output_text = _extract_reasoning_and_text(token)
                            if reasoning_text:
                                await websocket.send_text(
                                    json.dumps({"type": "reasoning", "data": reasoning_text, "agent": "main_agent"})
                                )
                            if output_text:
                                ai_response_parts.append(output_text)
                                await websocket.send_text(
                                    json.dumps({"type": "chunk", "data": output_text})
                                )

                    elif stream_mode == "custom":
                        if isinstance(chunk, dict):
                            if "chart" in chunk:
                                filename = os.path.basename(chunk["chart"])
                                chart_url = f"/charts/{filename}"
                                await websocket.send_text(
                                    json.dumps({"type": "chart", "data": chart_url})
                                )
                            elif "tasks" in chunk:
                                await websocket.send_text(
                                    json.dumps({
                                        "type": "tasks_split",
                                        "data": chunk["tasks"],
                                        "agent": chunk.get("agent", "deep_research_agent"),
                                    })
                                )
                            elif "text" in chunk:
                                await websocket.send_text(
                                    json.dumps({
                                        "type": "reasoning",
                                        "data": chunk["text"],
                                        "agent": chunk.get("agent", "sub_agent"),
                                    })
                                )

                await websocket.send_text(json.dumps({"type": "done"}))

                full_response = "".join(ai_response_parts)
                if full_response:
                    asyncio.create_task(
                        asyncio.to_thread(save_ai_message, session_id,full_response)
                    )
            except Exception as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": str(e)})
                )
    except WebSocketDisconnect:
        pass


@app.get("/")
async def get_index():
    return HTMLResponse(content=open("UI/index.html").read(), media_type="text/html")
