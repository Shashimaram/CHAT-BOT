from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_pie_chart(
    query: str,
    theme: str = "default",
    width: int = 8,
    height: int = 8,
    title: str = ""
) -> str:
    """
    Generates a pie chart to show the proportions of different categories in a whole.
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'type': The label for the category.
            - 'value': The numeric value representing the size of the slice.
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 8.
        height (int): Figure height in inches. Default is 8.
        title (str): Main title of the chart.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    fig, ax = plt.subplots(figsize=(width, height))
    
    ax.pie(df['value'], labels=df['type'], autopct='%1.1f%%', startangle=140)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    apply_common_style(ax, title, theme=theme)
    
    return fig_to_base64(fig, title)

