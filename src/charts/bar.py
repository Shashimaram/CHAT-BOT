from strands import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_bar_chart(
    query: str,
    theme: str = "default",
    width: int = 10,
    height: int = 6,
    title: str = "",
    axisXTitle: str = "",
    axisYTitle: str = ""
) -> str:
    """
    Generates a bar chart for comparing quantities across different categories.
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'x': The category name or label.
            - 'y': The numeric value for that category.
            - 'group' (optional): A string to create grouped or stacked bars.
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
        pivot_df = df.pivot(index='x', columns='group', values='y')
        pivot_df.plot(kind='bar', ax=ax)
    else:
        ax.bar(df['x'], df['y'])
    
    apply_common_style(ax, title, axisXTitle, axisYTitle, theme)
    plt.xticks(rotation=45)
    
    return fig_to_base64(fig, title)
    

