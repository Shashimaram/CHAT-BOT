from psycopg2.extensions import cursor
from strands import tool
from dotenv import load_dotenv
load_dotenv()
import os
import json
import psycopg2

def check_query_safety(query: str) -> bool:
    """
    Checks if the query is safe to execute.
    """
    dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"]
    for keyword in dangerous_keywords:
        if keyword.lower() in query.lower():
            return False
    return True


@tool
def execute_query(query: str) -> str:
    """
    Executes a given SQL query on the billing data table and returns the results. 

    # Important:
    This is a Postgress database

    Args:
        query (str): The SQL query to be executed.
    Returns:
        A string representation of the query results.   
    """
    # Establish a connection to the ClickHouse database
    try:
        
        USER = os.getenv("user")
        PASSWORD = os.getenv("password")
        HOST = os.getenv("host")
        PORT = os.getenv("port")
        DBNAME = os.getenv("dbname")
        if not check_query_safety(query):
            return "Query is not safe to execute"
        else:
            connection = psycopg2.connect(user=USER,password=PASSWORD,host=HOST,port=PORT,dbname=DBNAME)
            cursor = connection.cursor()
            cursor.execute(query=query)
            results = cursor.fetchall()
            return results

    except Exception as e:
        print(e)

