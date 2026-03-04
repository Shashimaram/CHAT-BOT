import re
from langchain_core.tools import tool
from langchain_core.messages import AIMessageChunk
from langchain.agents import create_agent
from langgraph.config import get_stream_writer
from src.model import bedrock_model
from src.tools.read_schema_tool import read_schema_tool
from src.tools.execute_query import execute_query

_CHART_PATH_RE = re.compile(r"generated_charts[\\/][^\s\"'<>]+\.png")
from src.charts import (
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
    generate_word_cloud_chart,
)

VISUALIZATION_PROMPT = """
You are a Data visualization agent. Visualize data using one of the available chart tools.

Rules:
1. Visualize data in a way that is easy to understand.
2. Limit to 1-2 charts only per request.

Charts available: generate_line_chart, generate_area_chart, generate_bar_chart, generate_boxplot_chart, generate_column_chart, generate_funnel_chart, generate_histogram_chart, generate_liquid_chart, generate_network_graph_chart, generate_pie_chart, generate_radar_chart, generate_scatter_chart, generate_treemap_chart, generate_venn_chart, generate_waterfall_chart, generate_word_cloud_chart.

Pass the SQL query and parameters to the chart tools. Example: generate_line_chart(query="select * from aws_oci_testing_data limit 10", theme="default", width=10, height=6, title="Line Chart", axisXTitle="Time", axisYTitle="Value")
"""


def _create_visualization_agent():
    return create_agent(
        model=bedrock_model,
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
            generate_word_cloud_chart,
        ],
        system_prompt=VISUALIZATION_PROMPT,
    )


@tool
async def visualization_agent(query: str) -> str:
    """Data visualization agent that visualizes data using available chart tools."""
    writer = get_stream_writer()
    writer({"agent": "visualization_agent", "text": "Creating visualization..."})

    try:
        agent = _create_visualization_agent()
        chart_paths: list[str] = []
        result_content = ""

        async for mode, chunk in agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode=["messages", "updates"],
        ):
            if mode == "messages":
                token, metadata = chunk
                if isinstance(token, AIMessageChunk) and token.text:
                    writer({"agent": "visualization_agent", "text": token.text})
            elif mode == "updates":
                for node, update in chunk.items():
                    if "messages" not in update:
                        continue
                    for msg in update["messages"]:
                        content = msg.content if hasattr(msg, "content") else str(msg)
                        if isinstance(content, str):
                            for path in _CHART_PATH_RE.findall(content):
                                if path not in chart_paths:
                                    chart_paths.append(path)
                                    writer({"agent": "visualization_agent", "chart": path})
                    if update["messages"]:
                        last = update["messages"][-1].content
                        result_content = last if isinstance(last, str) else str(last)

        if chart_paths:
            paths_str = "\n".join(chart_paths)
            result_content = f"{paths_str}\n\n{result_content}"

        return result_content or "No result"
    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"Error: {e}"


# Backward compatibility alias
visualiation_agent = visualization_agent
