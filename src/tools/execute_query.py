from psycopg2.extensions import cursor
from strands import tool
from dotenv import load_dotenv
load_dotenv()
import os
import json
import psycopg2


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
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")
    connection = psycopg2.connect(user=USER,password=PASSWORD,host=HOST,port=PORT,dbname=DBNAME)
    cursor = connection.cursor()
    cursor.execute(query=query)
    results = cursor.fetchall()
    return results


