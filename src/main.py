from agents import research_agent, visualiation_agent
from strands import Agent
from model import bedrock_model
from tools.utils import Initialize_table_details
from strands_tools import handoff_to_user

Main_prompt = """
You are a main coordinator agent that helps users with data analysis and visualization tasks.
You have access to two specialized agents:
1. research_agent - Use this to analyze data, execute queries, and answer analytical questions
2. visualiation_agent - Use this to create visualizations and charts from data

Delegate tasks to the appropriate agent based on the user's request.

ALway ask USER before visualization
"""

# generate_schema =Initialize_table_details()
# generate_schema.generate_schema_description()


import asyncio

main_agent  = Agent(
    model=bedrock_model,
    name="main_agent",
    tools=[
        research_agent,
        visualiation_agent,
        handoff_to_user
    ],
    system_prompt=Main_prompt,
)






async def run_swarm():
    query = input("Enter your query: ")
    result = await main_agent.invoke_async(query)
    return result

result = asyncio.run(run_swarm())
