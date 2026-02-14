from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_boxplot_chart(
    query: str,
    theme: str = "default",
    width: int = 10,
    height: int = 6,
    title: str = "",
    axisXTitle: str = "",
    axisYTitle: str = ""
) -> str:
    """
    Generates a boxplot chart to visualize the distribution and outliers of data across groups.
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'group': The name of the group/category for the box.
            - 'value': A numeric value belonging to that group.
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
    
    groups = df['group'].unique()
    plot_data = [df[df['group'] == g]['value'] for g in groups]
    
    ax.boxplot(plot_data, labels=groups)
    
    apply_common_style(ax, title, axisXTitle, axisYTitle, theme)
    
    return fig_to_base64(fig, title)

