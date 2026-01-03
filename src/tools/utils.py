from pathlib import Path
import sys
# Add the parent directory to the path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from strands import Agent,tool
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from dotenv import load_dotenv
from .execute_query import execute_query
load_dotenv()
import os
import json


from src.model import bedrock_model
import psycopg2


class ColumnSchema(BaseModel):
    """Schema for individual column details"""
    column_name: str = Field(description="Name of the column")
    data_type: str = Field(description="Data type of the column")
    max_length: Optional[int] = Field(None, description="Maximum character length if applicable")
    is_nullable: str = Field(description="Whether the column accepts NULL values")
    default_value: Optional[str] = Field(None, description="Default value for the column")
    description: Optional[str] = Field(None, description="AI-generated description of this column")
    
class TableSchema(BaseModel):
    """Complete schema for a database table"""
    table_name: str = Field(description="Name of the table")
    description: str = Field(description="AI-generated description of the table's purpose")
    columns: List[ColumnSchema] = Field(description="List of all columns in the table")

class Initialize_table_details:

    def __init__(self) -> None:
        USER = os.getenv("user")
        PASSWORD = os.getenv("password")
        HOST = os.getenv("host")
        PORT = os.getenv("port")
        DBNAME = os.getenv("dbname")
        print(f"Initializing database connection to {HOST}:{PORT}/{DBNAME}")
        self.connection = psycopg2.connect(user=USER,password=PASSWORD,host=HOST,port=PORT,dbname=DBNAME)
        self.table_names = []
        self.table_schemas = {}
        print("Database connection established successfully")
        


    def _get_table_names_from_database(self,):
        try:
            cursor = self.connection.cursor()
            query = "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            cursor.execute(query=query)
            result = cursor.fetchall()
            self.table_names = [table[0] for table in result ]
            print(f"Found {len(self.table_names)} tables in database: {', '.join(self.table_names)}")
            cursor.close()
        
        except Exception as e:
            print(e)
    

    def _getting_table_description(self):
        try:
            self._get_table_names_from_database()
            cursor = self.connection.cursor()
            # Query to describe table structure
            for table in self.table_names:
                print(f"Analyzing schema for table: {table}")
                query = f"""SELECT column_name,data_type,character_maximum_length,is_nullable, column_default FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position;"""
                cursor.execute(query)
                result = cursor.fetchall()
                schema = {}
                
                
                # Print column information
                for row in result:
                    schema[row[0]] = f"Type: {row[1]}, Max Length: {row[2]}, Nullable: {row[3]}, Default: {row[4]}"

                self.table_schemas[table] = schema

            cursor.close()
            self.connection.close()
        
        except Exception as e:
            print(e)
    



    def generate_schema_description(self):

        try:
            self._getting_table_description()
            agent  = Agent(
                model=bedrock_model,
                tools=[execute_query],
                # structured_output_model=TableSchema,
                system_prompt="""You are a Specalist in Generating Description for table column names that help other agents
                Consider the table schema provided and use the Attached Tool to read the data in the table and provide Output in attached structure.
                
                The USE tool to Read ROW values if needed before generating description to and also consider sideby columns before generating the column description"""
                )

            tables = []
            for table_name in self.table_schemas:
                print(f"Generating AI description for table: {table_name}")
                Human_message = f"""Name of the table {str(table_name)} and {str(self.table_schemas[table_name])}"""
                result = agent.structured_output(output_model=TableSchema,prompt=Human_message)
                print("agent invoked")
                # Use model_dump() instead of model_dump_json() to get a dict, not a string
                tables.append(result.model_dump())
            
            with open("tables_schema.json", "w") as file:
                json.dump(tables, file, indent=2)
            
            print(f"Successfully generated schema descriptions for {len(tables)} tables and saved to tables_schema.json")
                
        
        except Exception as e:
            print(e)


    
    
