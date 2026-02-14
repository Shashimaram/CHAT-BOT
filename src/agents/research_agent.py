from langchain_core.tools import tool
from langchain.agents import create_agent
from src.model import bedrock_model
from src.tools.read_schema_tool import read_schema_tool, get_tables
from src.tools.execute_query import execute_query
from src.stream_context import get_stream_sink

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


async def _run_research_agent(question: str) -> str:
    agent = _create_research_agent()
    sink = get_stream_sink()
    result_content = ""

    if sink:
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": question}]},
        ):
            if event.get("event") == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk:
                    text = getattr(chunk, "text", None) or (
                        chunk.content if isinstance(getattr(chunk, "content", ""), str) else ""
                    )
                    if text:
                        await sink("research_agent", text)
            elif event.get("event") == "on_chain_end":
                output = event.get("data", {}).get("output")
                if output and isinstance(output, dict) and "messages" in output:
                    msgs = output["messages"]
                    if msgs:
                        last = msgs[-1]
                        result_content = last.content if hasattr(last, "content") else str(last)
    else:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": question}]})
        if result.get("messages"):
            last_msg = result["messages"][-1]
            result_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        else:
            result_content = str(result)

    return result_content


@tool
async def research_agent(question: str) -> str:
    """
    Data research agent that answers user questions by researching using attached tools. If you need to visualize data, use the visualization agent.
    """
    import traceback
    try:
        return await _run_research_agent(question)
    except Exception as e:
        traceback.print_exc()
        return f"Error: {e}"
    
