from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from src.model import bedrock_model
from src.agents.research_agent import research_agent
from src.agents.visualization_agent import visualization_agent
from src.tools.utils import Initialize_table_details

PROMPT = """You are a supervisor agent that delegates user requests to the right specialist.

Available tools:
- research_agent: Pass the user's question directly to this tool for any data lookup, analysis, or SQL research task. It will query the database and return an answer.
- visualization_agent: Pass the user's request to this tool when they want a chart, graph, or visual representation of data.

Rules:
- Delegate immediately; do NOT attempt to query the database yourself.
- Pass the user's full question to the tool so it has complete context.
- Keep your own reply concise — summarize or relay the tool's answer without re-explaining everything."""

# In-memory checkpointer for conversation history per thread.
# Swap with PostgresSaver / DynamoDBSaver for production persistence.

# initializer = Initialize_table_details()
# initializer.generate_schema_description()


memory = MemorySaver()

main_agent = create_agent(
    checkpointer=memory,
    model=bedrock_model,
    tools=[research_agent, visualization_agent],
    system_prompt=PROMPT,
)