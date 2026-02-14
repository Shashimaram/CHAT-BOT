import re
from langchain_core.tools import tool
from langchain.agents import create_agent
from src.model import bedrock_model
from src.tools.read_schema_tool import read_schema_tool
from src.tools.execute_query import execute_query
from src.stream_context import get_stream_sink

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


async def _run_visualization_agent(query: str) -> str:
    agent = _create_visualization_agent()
    sink = get_stream_sink()
    result_content = ""
    chart_paths: list[str] = []  # collect chart file paths from tool results

    if sink:
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": query}]},
        ):
            if event.get("event") == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk:
                    text = getattr(chunk, "text", None) or (
                        chunk.content if isinstance(getattr(chunk, "content", ""), str) else ""
                    )
                    if text:
                        await sink("visualization_agent", text)
            elif event.get("event") == "on_tool_end":
                # Capture chart file paths from chart tool results
                output = event.get("data", {}).get("output")
                if output:
                    output_str = str(output)
                    chart_paths.extend(_CHART_PATH_RE.findall(output_str))
            elif event.get("event") == "on_chain_end":
                output = event.get("data", {}).get("output")
                if output and isinstance(output, dict) and "messages" in output:
                    msgs = output["messages"]
                    if msgs:
                        last = msgs[-1]
                        result_content = last.content if hasattr(last, "content") else str(last)
    else:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
        if result.get("messages"):
            # Scan all messages for chart paths
            for msg in result["messages"]:
                content = msg.content if hasattr(msg, "content") else str(msg)
                if isinstance(content, str):
                    chart_paths.extend(_CHART_PATH_RE.findall(content))
            last_msg = result["messages"][-1]
            result_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        else:
            result_content = str(result)

    # Prepend chart paths so the main agent's ToolMessage includes them
    if chart_paths:
        paths_str = "\n".join(chart_paths)
        result_content = f"{paths_str}\n\n{result_content}"

    return result_content


@tool
async def visualization_agent(query: str) -> str:
    """Data visualization agent that visualizes data using available chart tools."""
    import traceback
    try:
        return await _run_visualization_agent(query)
    except Exception as e:
        traceback.print_exc()
        return f"Error: {e}"


# Backward compatibility alias
visualiation_agent = visualization_agent
