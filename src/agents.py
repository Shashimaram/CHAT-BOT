from strands import Agent, tool
from model import bedrock_model
from tools.read_schema_tool import read_schema_tool, get_tables
from tools.execute_query import execute_query
from charts import *


Research_prompt = """
    You are a SQL research agent specialized in analyzing data from databases. You have three tools available: get_tables, read_schema_tool, and execute_query.
    
    Workflow:
    1. First, use get_tables to discover all available tables in the database.
    2. Use read_schema_tool to understand the structure and columns of relevant tables.
    3. Use execute_query to run SQL queries and retrieve data to answer the user's question.
    
    You can execute queries multiple times (up to 10) to iteratively explore and analyze the data as needed.
    If the user needs data visualization, delegate to the visualization agent.
    
    Always base your analysis on the actual table schemas and data available in the database.
    """

Visualization_prompt = """
    You are a Data visualization agent and you have to visualize the data using one of the available chart tools. table name :  aws_oci_testing_data
    You have to visualize the data in a way that is easy to understand and use for the user.
    You have following Charts available:
            generate_line_chart,
            generate_area_chart,
            generate_bar_chart,
            generate_boxplot_chart,
            generate_column_chart,
            generate_funnel_chart,
            generate_histogram_chart,
            generate_liquid_chart,
            generate_network_graph_chart,
            generate_pie_chart,
            generate_radar_chart,
            generate_scatter_chart,
            generate_treemap_chart,
            generate_venn_chart,
            generate_waterfall_chart,
            generate_word_cloud_chart

            You have to Pass the SQL query and  othere parameters to the chart tools to generate the chart.
            For example:
            generate_line_chart(query="select * from aws_oci_testing_data limit 10", theme="default", width=10, height=6, title="Line Chart", axisXTitle="Time", axisYTitle="Value")
    """


@tool
def research_agent(question: str) -> str:
    """
    You are a Data research agent and you have to answer the user question by researching using attached tools. If you need to visualize data, use the visualization agent.
    """
    try:

        research_agent  = Agent(
            model=bedrock_model,
            name="research_agent",
            tools=[
                read_schema_tool,
                get_tables,
                execute_query,
            ],
            system_prompt=Research_prompt,
        )
        return research_agent(question)
    except Exception as e:
        return f"Error: {e}"



@tool
def visualiation_agent(query: str) -> str:
    """
    USe this Tool to visualize the data, pass the Query the you used to get the the data and additional information and points to be considered  while visualizing the data.
    """
    try:
        visualization_agent = Agent(
            model=bedrock_model,
            name="visualization_agent",
            tools=[
                read_schema_tool,
                execute_query,
                generate_line_chart,
                generate_area_chart,
                generate_bar_chart,
                generate_boxplot_chart,
                generate_column_chart,
                generate_funnel_chart,
                generate_histogram_chart,
                generate_liquid_chart,
                generate_network_graph_chart,
                generate_pie_chart,
                generate_radar_chart,
                generate_scatter_chart,
                generate_treemap_chart,
                generate_venn_chart,
                generate_waterfall_chart,
                generate_word_cloud_chart
            ],
            system_prompt=Visualization_prompt,
        )
        return visualization_agent(query)
    except Exception as e:
        return f"Error: {e}"

