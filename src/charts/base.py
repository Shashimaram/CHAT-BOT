import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid thread issues
import matplotlib.pyplot as plt
import io
import psycopg2
import base64
import pandas as pd
import os
import time
from typing import Any, Dict, List, Optional

def get_data_from_query(query: str) -> pd.DataFrame:
    """Executes a SQL query and returns a pandas DataFrame."""
    connection = None
    cursor = None
    
    try:
        USER = os.getenv("user")
        PASSWORD = os.getenv("password")
        HOST = os.getenv("host")
        PORT = os.getenv("port")
        DBNAME = os.getenv("dbname")
        
        connection = psycopg2.connect(user=USER,password=PASSWORD,host=HOST,port=PORT,dbname=DBNAME)
        cursor = connection.cursor()
        cursor.execute(query=query)
        results = cursor.fetchall()
        # Convert the results to a pandas DataFrame the result is list of tuples
        df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
        return df
        
    except psycopg2.Error as db_error:
        raise Exception(f"Database error: {str(db_error)}")
    except Exception as e:
        raise Exception(f"Error executing query: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def fig_to_base64(fig, title: Optional[str] = None):
    """Converts a matplotlib figure to a base64 encoded PNG string and saves it to a file."""
    # Ensure directory exists
    output_dir = "generated_charts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate filename
    if title:
        # Sanitize title for filename
        clean_title = "".join([c if c.isalnum() else "_" for c in title])
        filename = f"{clean_title}_{int(time.time())}.png"
    else:
        filename = f"chart_{int(time.time())}.png"
    
    filepath = os.path.join(output_dir, filename)
    fig.savefig(filepath, format='png', bbox_inches='tight')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_str}"

def apply_common_style(ax, title=None, xlabel=None, ylabel=None, theme="default"):
    """Applies common styling to a matplotlib axis."""
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    
    if theme == "dark":
        ax.set_facecolor('#2c2c2c')
        ax.figure.set_facecolor('#2c2c2c')
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
    elif theme == "academy":
        # Simplified academy style
        ax.grid(True, linestyle='--', alpha=0.7)
