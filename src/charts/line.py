from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_line_chart(
    query: str,
    theme: str = "default",
    width: int = 10,
    height: int = 6,
    title: str = "",
    axisXTitle: str = "",
    axisYTitle: str = ""
) -> str:
    """
    Generates a line chart to visualize trends over time or continuous categories.
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'time': The x-axis value (e.g., date, year, or sequence).
            - 'value': The numeric y-axis value.
            - 'group' (optional): A string to categorize data into multiple lines.
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
    
    if 'group' in df.columns:
        for label, group_df in df.groupby('group'):
            ax.plot(group_df['time'], group_df['value'], label=label, marker='o')
        ax.legend()
    else:
        ax.plot(df['time'], df['value'], marker='o')
    
    apply_common_style(ax, title, axisXTitle, axisYTitle, theme)
    plt.xticks(rotation=45)
    
    return fig_to_base64(fig, title)
