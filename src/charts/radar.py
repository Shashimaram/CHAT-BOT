from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_radar_chart(
    query: str,
    theme: str = "default",
    width: int = 8,
    height: int = 8,
    title: str = ""
) -> str:
    """
    Generates a radar (spider) chart to compare multiple quantitative variables across categories.
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'item': The dimension or variable name (e.g., 'Speed', 'Quality').
            - 'score': The numeric value for that dimension.
            - 'group' (optional): A string to create multiple layers (e.g., 'Product A', 'Product B').
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 8.
        height (int): Figure height in inches. Default is 8.
        title (str): Main title of the chart.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    items = df['item'].unique()
    num_vars = len(items)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(width, height), subplot_kw=dict(polar=True))

    if 'group' in df.columns:
        for group in df['group'].unique():
            values = df[df['group'] == group]['score'].tolist()
            values += values[:1]
            ax.plot(angles, values, label=group)
            ax.fill(angles, values, alpha=0.25)
        ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    else:
        values = df['score'].tolist()
        values += values[:1]
        ax.plot(angles, values)
        ax.fill(angles, values, alpha=0.25)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(items)

    apply_common_style(ax, title, theme=theme)

    
    return fig_to_base64(fig, title)

