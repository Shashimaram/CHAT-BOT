from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_liquid_chart(
    query: str,
    theme: str = "default",
    width: int = 6,
    height: int = 6,
    title: str = ""
) -> str:
    """
    Generates a liquid chart (a circular gauge) to show a percentage or ratio.
    
    Args:
        query (str): The SQL query to fetch a single numeric value between 0 and 1.
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 6.
        height (int): Figure height in inches. Default is 6.
        title (str): Main title of the chart.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    value = float(df.iloc[0, 0])
    fig, ax = plt.subplots(figsize=(width, height))
    
    circle = plt.Circle((0.5, 0.5), 0.4, color='blue', fill=False, linewidth=2)
    ax.add_artist(circle)
    
    # Fill based on value (0 to 1)
    # Simplified as a rectangle clipped by the circle
    rect = plt.Rectangle((0.1, 0.1), 0.8, 0.8 * value, color='blue', alpha=0.5)
    ax.add_artist(rect)
    
    ax.text(0.5, 0.5, f"{int(value*100)}%", ha='center', va='center', fontsize=20, fontweight='bold')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    apply_common_style(ax, title, theme=theme)
    
    return fig_to_base64(fig, title)

