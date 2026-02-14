import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid thread issues
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Absolute path to project root (Building_bot/) so charts always land in one place
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

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
    """Saves a matplotlib figure to disk and returns the file path.

    The function name is kept for backward compatibility with all chart modules.
    """
    output_dir = _PROJECT_ROOT / "generated_charts"
    output_dir.mkdir(exist_ok=True)

    if title:
        clean_title = "".join([c if c.isalnum() else "_" for c in title])
        filename = f"{clean_title}_{int(time.time())}.png"
    else:
        filename = f"chart_{int(time.time())}.png"

    filepath = output_dir / filename
    fig.savefig(str(filepath), format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)

    # Return relative path from project root — backend serves it as /charts/<filename>
    return f"generated_charts/{filename}"

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
