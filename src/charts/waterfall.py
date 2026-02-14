from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_waterfall_chart(
    query: str,
    theme: str = "default",
    width: int = 10,
    height: int = 6,
    title: str = "",
    axisXTitle: str = "",
    axisYTitle: str = ""
) -> str:
    """
    Generates a waterfall chart to show how an initial value is affected by positive and negative changes.
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'label': The name of the change or step.
            - 'value': The numeric change (positive or negative).
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 10.
        height (int): Figure height in inches. Default is 6.
        title (str): Main title of the chart.
        axisXTitle (str): Label for the horizontal axis.
        axisYTitle (str): Label for the vertical axis.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    fig, ax = plt.subplots(figsize=(width, height))
    
    cumulative = df['value'].cumsum()
    bottom = cumulative.shift(1).fillna(0)
    
    colors = ['green' if x >= 0 else 'red' for x in df['value']]
    
    ax.bar(df['label'], df['value'], bottom=bottom, color=colors)
    
    # Add connecting lines
    for i in range(len(df) - 1):
        ax.plot([i, i + 1], [cumulative[i], cumulative[i]], color='gray', linestyle='--', linewidth=0.5)

    apply_common_style(ax, title, axisXTitle, axisYTitle, theme)
    plt.xticks(rotation=45)
    
    return fig_to_base64(fig, title)

