from langchain_core.tools import tool
import traceback
from langchain_core.messages import AIMessageChunk
from langchain.agents import create_agent
from langgraph.config import get_stream_writer
from src.model import bedrock_model
from src.tools.read_schema_tool import read_schema_tool, get_tables
from src.tools.execute_query import execute_query

RESEARCH_PROMPT = """
You are a fast SQL research agent. Answer the user's question using the database.

Tools: get_tables, read_schema_tool, execute_query.

Workflow (be efficient — minimize tool calls):
1. Call get_tables ONCE to see table names, descriptions and column names.
2. Only call read_schema_tool if you need full column details (data types, nullability) for a specific table. Skip it if column names from get_tables are enough to write the query.
3. Write a precise SQL query with LIMIT (default LIMIT 50 unless the user asks for more). Execute it with execute_query.
4. Return a clear, concise answer based on the results. Do NOT re-run queries unnecessarily.

Important:
- Always use LIMIT to avoid huge result sets.
- Prefer a single well-crafted query over multiple exploratory ones.
- Keep answers brief and data-focused.
"""


def _create_research_agent():
    return create_agent(
        model=bedrock_model,
        tools=[read_schema_tool, get_tables, execute_query],
        system_prompt=RESEARCH_PROMPT,
    )


@tool
async def research_agent(question: str) -> str:
    """Data research agent that answers user questions by researching using attached tools. If you need to visualize data, use the visualization agent."""
    writer = get_stream_writer()
    writer({"agent": "research_agent", "text": "Researching your question..."})

    try:
        agent = _create_research_agent()
        result_content = ""

        async for mode, chunk in agent.astream(
            {"messages": [{"role": "user", "content": question}]},stream_mode=["messages", "updates"],):

            if mode == "messages":
                token, _ = chunk
                if isinstance(token, AIMessageChunk) and token.text:
                    writer({"agent": "research_agent", "text": token.text})
            elif mode == "updates":
                for node, update in chunk.items():
                    if "messages" in update and update["messages"]:
                        content = update["messages"][-1].content
                        result_content = content if isinstance(content, str) else str(content)

        return result_content or "No result"
    except Exception as e:
        traceback.print_exc()
        return f"Error: {e}"