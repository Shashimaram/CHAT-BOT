from strands import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_histogram_chart(
    query: str,
    bins: int = 10,
    theme: str = "default",
    width: int = 10,
    height: int = 6,
    title: str = "",
    axisXTitle: str = "",
    axisYTitle: str = "Frequency"
) -> str:
    """
    Generates a histogram to visualize the distribution of a numeric dataset.
    
    Args:
        query (str): The SQL query to fetch data. Expected to return a column named 'value'.
        bins (int): The number of intervals (bins) to use for the distribution. Default is 10.
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 10.
        height (int): Figure height in inches. Default is 6.
        title (str): Main title of the chart.
        axisXTitle (str): Label for the horizontal axis.
        axisYTitle (str): Label for the vertical axis. Default is 'Frequency'.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    data = df['value'].tolist()
    fig, ax = plt.subplots(figsize=(width, height))
    
    ax.hist(data, bins=bins, edgecolor='black', alpha=0.7)
    
    apply_common_style(ax, title, axisXTitle, axisYTitle, theme)
    
    return fig_to_base64(fig, title)

