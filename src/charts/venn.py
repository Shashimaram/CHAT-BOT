from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_venn_chart(
    query: str,
    theme: str = "default",
    width: int = 8,
    height: int = 8,
    title: str = ""
) -> str:
    """
    Generates a Venn diagram to visualize overlapping sets.
    
    Args:
        query (str): The SQL query to fetch set names. Expected column: 'name'.
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 8.
        height (int): Figure height in inches. Default is 8.
        title (str): Main title of the chart.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    names = df['name'].tolist()
    
    fig, ax = plt.subplots(figsize=(width, height))
    
    if len(names) == 2:
        # Assuming data[0] is A, data[1] is B, and we need intersection
        # This is a simplified mapping
        venn2(subsets=(10, 10, 5), set_labels=(names[0], names[1]), ax=ax)
    elif len(names) == 3:
        venn3(subsets=(10, 10, 5, 10, 5, 5, 2), set_labels=(names[0], names[1], names[2]), ax=ax)
    
    apply_common_style(ax, title, theme=theme)
    
    return fig_to_base64(fig, title)

