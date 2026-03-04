import json
import logging
import os
import uuid
from datetime import datetime, timezone

import psycopg2
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

load_dotenv()

TABLE_NAME = "chat_history"

_conn = None
_storage_backend = "db"  # "db" or "memory"
_memory_sessions = {}  # session_id -> list of {"role", "content", "created_at"} for list_sessions


def _get_connection():
    global _conn
    if _storage_backend != "db":
        return None
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(
            host=os.getenv("host"),
            port=int(os.getenv("port", "5432")),
            dbname=os.getenv("dbname"),
            user=os.getenv("user"),
            password=os.getenv("password"),
        )
        _conn.autocommit = True
    return _conn


def init_chat_history():
    global _storage_backend
    try:
        conn = _get_connection()
        if conn is None:
            return
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    message JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_session_id
                ON {TABLE_NAME} (session_id)
            """)
    except Exception as e:
        logging.getLogger(__name__).warning(
            "Database unavailable (%s), using in-memory chat history.", e
        )
        _storage_backend = "memory"


def create_session() -> str:
    return str(uuid.uuid4())


def _serialize_message(msg) -> dict:
    if isinstance(msg, HumanMessage):
        return {"type": "human", "data": {"content": msg.content}}
    elif isinstance(msg, AIMessage):
        return {"type": "ai", "data": {"content": msg.content}}
    elif isinstance(msg, SystemMessage):
        return {"type": "system", "data": {"content": msg.content}}
    return {"type": "unknown", "data": {"content": str(msg)}}


def _deserialize_message(row: dict):
    msg_type = row.get("type", "")
    content = row.get("data", {}).get("content", "")
    if msg_type == "human":
        return HumanMessage(content=content)
    elif msg_type == "ai":
        return AIMessage(content=content)
    elif msg_type == "system":
        return SystemMessage(content=content)
    return HumanMessage(content=content)


def save_user_message(session_id: str, content: str):
    msg = _serialize_message(HumanMessage(content=content))
    if _storage_backend == "memory":
        _memory_sessions.setdefault(session_id, []).append({
            "role": "user",
            "content": content,
            "created_at": datetime.now(timezone.utc),
        })
        return
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {TABLE_NAME} (session_id, message) VALUES (%s, %s)",
            (session_id, json.dumps(msg)),
        )


def save_ai_message(session_id: str, content: str):
    msg = _serialize_message(AIMessage(content=content))
    if _storage_backend == "memory":
        _memory_sessions.setdefault(session_id, []).append({
            "role": "assistant",
            "content": content,
            "created_at": datetime.now(timezone.utc),
        })
        return
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {TABLE_NAME} (session_id, message) VALUES (%s, %s)",
            (session_id, json.dumps(msg)),
        )


def load_session_messages(session_id: str) -> list[dict]:
    if _storage_backend == "memory":
        rows = _memory_sessions.get(session_id, [])
        return [{"role": r["role"], "content": r["content"]} for r in rows]
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT message FROM {TABLE_NAME} WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,),
        )
        rows = cur.fetchall()

    results = []
    for (raw,) in rows:
        data = raw if isinstance(raw, dict) else json.loads(raw)
        msg_type = data.get("type", "")
        content = data.get("data", {}).get("content", "")
        results.append({
            "role": "user" if msg_type == "human" else "assistant",
            "content": content,
        })
    return results


def list_sessions() -> list[dict]:
    if _storage_backend == "memory":
        out = []
        for sid, messages in _memory_sessions.items():
            first_user = next((m["content"] for m in messages if m["role"] == "user"), "New chat")
            created = messages[0]["created_at"] if messages else None
            last_ts = messages[-1]["created_at"] if messages else None
            out.append({
                "session_id": sid,
                "started_at": created.isoformat() if created else None,
                "last_active": last_ts.isoformat() if last_ts else None,
                "preview": (first_user or "New chat")[:100],
            })
        out.sort(key=lambda x: x["last_active"] or "", reverse=True)
        return out
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(f"""
            WITH session_info AS (
                SELECT session_id,
                       MIN(created_at) AS started_at,
                       MAX(created_at) AS last_active
                FROM {TABLE_NAME}
                GROUP BY session_id
            ),
            first_msg AS (
                SELECT DISTINCT ON (session_id)
                       session_id,
                       message->'data'->>'content' AS preview
                FROM {TABLE_NAME}
                WHERE message->>'type' = 'human'
                ORDER BY session_id, created_at ASC
            )
            SELECT s.session_id, s.started_at, s.last_active,
                   COALESCE(f.preview, 'New chat')
            FROM session_info s
            LEFT JOIN first_msg f ON s.session_id = f.session_id
            ORDER BY s.last_active DESC
        """)
        return [
            {
                "session_id": row[0],
                "started_at": row[1].isoformat() if row[1] else None,
                "last_active": row[2].isoformat() if row[2] else None,
                "preview": (row[3] or "New chat")[:100],
            }
            for row in cur.fetchall()
        ]


def delete_session(session_id: str):
    if _storage_backend == "memory":
        _memory_sessions.pop(session_id, None)
        return
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {TABLE_NAME} WHERE session_id = %s",
            (session_id,),
        )
