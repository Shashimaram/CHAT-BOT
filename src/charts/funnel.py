from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_funnel_chart(
    query: str,
    theme: str = "default",
    width: int = 10,
    height: int = 6,
    title: str = ""
) -> str:
    """
    Generates a funnel chart to visualize stages in a process (e.g., sales conversion).
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'stage': The name of the process step.
            - 'value': The numeric value at that step.
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 10.
        height (int): Figure height in inches. Default is 6.
        title (str): Main title of the chart.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    labels = df['stage'].tolist()
    values = df['value'].tolist()
    
    # Calculate widths for the funnel stages
    max_val = max(values)
    widths = [v / max_val for v in values]
    
    fig, ax = plt.subplots(figsize=(width, height))
    
    y_pos = range(len(labels), 0, -1)
    for i, (label, width) in enumerate(zip(labels, widths)):
        # Centered horizontal bars
        ax.barh(y_pos[i], width, left=(1-width)/2, height=0.8, label=label)
        ax.text(0.5, y_pos[i], f"{label}: {values[i]}", ha='center', va='center', fontweight='bold')

    ax.set_xlim(0, 1)
    ax.axis('off')
    
    apply_common_style(ax, title, theme=theme)
    
    return fig_to_base64(fig, title)

