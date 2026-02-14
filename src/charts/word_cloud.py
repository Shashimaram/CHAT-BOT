from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from .base import fig_to_base64, get_data_from_query

@tool
def generate_word_cloud_chart(
    query: str,
    theme: str = "default",
    width: int = 10,
    height: int = 6,
    title: str = ""
) -> str:
    """
    Generates a word cloud to visualize word frequency or importance.
    
    Args:
        query (str): The SQL query to fetch data. Expected columns:
            - 'name': The word or term.
            - 'value': The weight, frequency, or importance of the word.
        theme (str): Visual style ('default', 'dark', 'academy').
        width (int): Figure width in inches. Default is 10.
        height (int): Figure height in inches. Default is 6.
        title (str): Main title of the chart.
        
    Returns:
        str: A base64-encoded PNG image string (data URI).
    """
    df = get_data_from_query(query)
    word_freq = dict(zip(df['name'], df['value']))
    
    bg_color = 'white' if theme != 'dark' else '#2c2c2c'
    
    wc = WordCloud(width=width*100, height=height*100, background_color=bg_color).generate_from_frequencies(word_freq)
    
    fig, ax = plt.subplots(figsize=(width, height))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    if title:
        ax.set_title(title, color='white' if theme == 'dark' else 'black')
    
    return fig_to_base64(fig, title)

