from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()
import os
import json

def check_query_safety(query: str) -> bool:
    """
    Checks if the query is safe to execute.
    """
    dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"]
    for keyword in dangerous_keywords:
        if keyword.lower() in query.lower():
            return False
    return True

def _get_database_connection():
    """
    Establishes a database connection to either PostgreSQL or SQL Server.
    Tries PostgreSQL first, then falls back to SQL Server.
    
    Returns:
        tuple: (connection, db_type) where db_type is 'postgresql' or 'sqlserver'
    """
    # Check for PostgreSQL environment variables
    pg_host = os.getenv("host")
    pg_port = os.getenv("port")
    pg_dbname = os.getenv("dbname")
    pg_user = os.getenv("user")
    pg_password = os.getenv("password")
    
    # Check for SQL Server environment variables
    sql_server = os.getenv("server")
    sql_database = os.getenv("database")
    sql_username = os.getenv("username")
    
    # Try PostgreSQL connection first
    if pg_host and pg_dbname and pg_user and pg_password:
        try:
            import psycopg2
            connection = psycopg2.connect(
                user=pg_user,
                password=pg_password,
                host=pg_host,
                port=pg_port or "5432",
                dbname=pg_dbname
            )
            return connection, "postgresql"
        except ImportError:
            pass  # psycopg2 not installed, try SQL Server
        except Exception:
            pass  # Connection failed, try SQL Server
    
    # Try SQL Server connection
    if sql_server and sql_database and sql_username:
        try:
            import pyodbc
            sql_password = os.getenv("password")
            sql_driver = os.getenv("driver", "{ODBC Driver 17 for SQL Server}")
            
            connection_string = (
                f"DRIVER={sql_driver};"
                f"SERVER={sql_server};"
                f"DATABASE={sql_database};"
                f"UID={sql_username};"
                f"PWD={sql_password};"
            )
            
            connection = pyodbc.connect(connection_string)
            return connection, "sqlserver"
        except ImportError:
            pass  # pyodbc not installed
        except Exception:
            pass  # Connection failed
    
    # If we get here, no connection was established
    raise Exception(
        "Could not establish database connection. Please check your .env file.\n"
        "For PostgreSQL, provide: host, port, dbname, user, password\n"
        "For SQL Server, provide: server, database, username, password"
    )

@tool
def execute_query(query: str) -> str:
    """
    Executes a given SQL query on the database and returns the results.
    Automatically detects and connects to either PostgreSQL or SQL Server.
    
    Important:
    - Only SELECT queries are allowed for safety
    - This tool supports both PostgreSQL and SQL Server databases
    - The database type is automatically detected from environment variables
    
    Args:
        query (str): The SQL query to be executed (SELECT statements only).
    
    Returns:
        A string representation of the query results.   
    """
    connection = None
    cursor = None
    
    try:
        # Check query safety
        if not check_query_safety(query):
            return "Error: Query is not safe to execute. Only SELECT queries are allowed."
        
        # Establish connection
        connection, db_type = _get_database_connection()
        
        # Execute query
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Format results as string
        if not results:
            return "Query executed successfully. No rows returned."
        
        # Convert results to readable format
        result_str = f"Query returned {len(results)} row(s):\n\n"
        for i, row in enumerate(results, 1):
            result_str += f"Row {i}: {row}\n"
        
        return result_str
        
    except Exception as e:
        return f"Error executing query: {str(e)}"
    
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection:
            connection.close()