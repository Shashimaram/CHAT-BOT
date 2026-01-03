from strands import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import squarify
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_treemap_chart(
    query: str,
    theme: str = "default",
    width: int = 10,
    height: int = 6,
    title: str = ""
) -> str:
    """
    Generates a treemap to visualize hierarchical data using nested rectangles.
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'name': The label for the item.
            - 'value': The numeric value representing the size of the rectangle.
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 10.
        height (int): Figure height in inches. Default is 6.
        title (str): Main title of the chart.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    labels = [f"{row['name']}\n({row['value']})" for _, row in df.iterrows()]
    sizes = df['value'].tolist()
    
    fig, ax = plt.subplots(figsize=(width, height))
    
    squarify.plot(sizes=sizes, label=labels, alpha=.8, ax=ax)
    
    ax.axis('off')
    apply_common_style(ax, title, theme=theme)
    
    return fig_to_base64(fig, title)

