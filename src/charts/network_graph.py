from strands import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import networkx as nx
from .base import fig_to_base64, apply_common_style, get_data_from_query

@tool
def generate_network_graph_chart(
    query_nodes: str,
    query_edges: str,
    theme: str = "default",
    width: int = 10,
    height: int = 8,
    title: str = ""
) -> str:
    """
    Generates a network graph to visualize connections between different entities.
    
    Args:
        query_nodes (str): SQL query to fetch nodes. Expected column: 'name'.
        query_edges (str): SQL query to fetch edges. Expected columns: 'source', 'target'.
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 10.
        height (int): Figure height in inches. Default is 8.
        title (str): Main title of the chart.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df_nodes = get_data_from_query(query_nodes)
    df_edges = get_data_from_query(query_edges)
    
    G = nx.Graph()
    for _, node in df_nodes.iterrows():
        G.add_node(node['name'])
    for _, edge in df_edges.iterrows():
        G.add_edge(edge['source'], edge['target'])
        
    fig, ax = plt.subplots(figsize=(width, height))
    pos = nx.spring_layout(G)
    
    node_color = 'skyblue' if theme != 'dark' else 'orange'
    nx.draw(G, pos, with_labels=True, node_color=node_color, node_size=2000, font_size=10, ax=ax)
    
    apply_common_style(ax, title, theme=theme)
    

    return fig_to_base64(fig, title)

