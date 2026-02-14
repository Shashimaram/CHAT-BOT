from pathlib import Path
import sys
# Add the parent directory to the path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from strands import Agent,tool
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import psycopg2
from dotenv import load_dotenv
from .execute_query import execute_query
load_dotenv()
import os
import json

from src.model import bedrock_model_custom

# --- Output directory for the schema file ---
SCHEMA_OUTPUT_PATH = Path(__file__).parent.parent / "tables_schema.json"

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

# --- Pydantic models ---

class ColumnSchema(BaseModel):
    """Schema for individual column details"""
    column_name: str = Field(description="Name of the column")
    data_type: str = Field(description="Data type of the column")
    max_length: Optional[int] = Field(None, description="Maximum character length if applicable")
    is_nullable: str = Field(description="Whether the column accepts NULL values")
    default_value: Optional[str] = Field(None, description="Default value for the column")
    description: Optional[str] = Field(None, description="AI-generated description of this column")


class RelationshipSchema(BaseModel):
    """Schema for a foreign key relationship between tables"""
    column: str = Field(description="Column in this table that holds the foreign key")
    references_table: str = Field(description="The table that this column references")
    references_column: str = Field(description="The column in the referenced table")


class TableSchema(BaseModel):
    """Complete schema for a database table"""
    table_name: str = Field(description="Name of the table")
    description: str = Field(description="AI-generated description of the table's purpose")
    columns: List[ColumnSchema] = Field(description="List of all columns in the table")
    relationships: Optional[List[RelationshipSchema]] = Field(
        default=None,
        description="Foreign key relationships this table has with other tables"
    )


class Initialize_table_details:

    def __init__(self) -> None:
        self.connection = None
        self.db_type = None  # Will be 'postgresql' or 'sqlserver'
        self.table_names: List[str] = []
        self.table_schemas: Dict[str, dict] = {}
        self.table_relationships: Dict[str, List[dict]] = {}  # table -> list of FK relationships
        
        # Try to connect to database
        self._establish_connection()

    def _establish_connection(self):
        """Try PostgreSQL first, then SQL Server based on available environment variables"""
        
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
                print(f"Attempting PostgreSQL connection to {pg_host}:{pg_port}/{pg_dbname}")
                self.connection = psycopg2.connect(
                    user=pg_user,
                    password=pg_password,
                    host=pg_host,
                    port=pg_port or "5432",
                    dbname=pg_dbname
                )
                self.db_type = "postgresql"
                print("✓ PostgreSQL connection established successfully")
                return
            except ImportError:
                print("⚠ psycopg2 not installed, trying SQL Server...")
            except Exception as e:
                print(f"⚠ PostgreSQL connection failed: {e}")
                print("Trying SQL Server...")
        
        # Try SQL Server connection
        if sql_server and sql_database and sql_username:
            try:
                import pyodbc
                sql_password = os.getenv("password")
                sql_driver = os.getenv("driver", "{ODBC Driver 17 for SQL Server}")
                
                print(f"Attempting SQL Server connection to {sql_server}/{sql_database}")
                
                connection_string = (
                    f"DRIVER={sql_driver};"
                    f"SERVER={sql_server};"
                    f"DATABASE={sql_database};"
                    f"UID={sql_username};"
                    f"PWD={sql_password};"
                )
                
                self.connection = pyodbc.connect(connection_string)
                self.db_type = "sqlserver"
                print("✓ SQL Server connection established successfully")
                return
            except ImportError:
                print("⚠ pyodbc not installed")
            except Exception as e:
                print(f"⚠ SQL Server connection failed: {e}")
        
        # If we get here, no connection was established
        raise Exception(
            "Could not establish database connection. Please check your .env file.\n"
            "For PostgreSQL, provide: host, port, dbname, user, password\n"
            "For SQL Server, provide: server, database, username, password"
        )

    # ------------------------------------------------------------------ #
    #  Step 1 – Discover tables
    # ------------------------------------------------------------------ #
    def _get_table_names_from_database(self):
        try:
            cursor = self.connection.cursor()
            
            if self.db_type == "postgresql":
                query = "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                cursor.execute(query)
            else:  # sqlserver
                query = """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE' 
                    AND TABLE_SCHEMA = 'dbo'
                    ORDER BY TABLE_NAME
                """
                cursor.execute(query)
            
            result = cursor.fetchall()
            self.table_names = [table[0] for table in result]
            print(f"Found {len(self.table_names)} tables in {self.db_type} database: {', '.join(self.table_names)}")
            cursor.close()
        except Exception as e:
            print(f"Error getting table names: {e}")

    # ------------------------------------------------------------------ #
    #  Step 2 – Get column metadata for every table
    # ------------------------------------------------------------------ #
    def _getting_table_description(self):
        try:
            self._get_table_names_from_database()
            cursor = self.connection.cursor()
            
            for table in self.table_names:
                print(f"Analyzing schema for table: {table}")
                
                if self.db_type == "postgresql":
                    query = f"""
                        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = '{table}'
                        ORDER BY ordinal_position;
                    """
                    cursor.execute(query)
                else:  # sqlserver
                    query = """
                        SELECT 
                            COLUMN_NAME, 
                            DATA_TYPE, 
                            CHARACTER_MAXIMUM_LENGTH, 
                            IS_NULLABLE, 
                            COLUMN_DEFAULT
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = ? 
                        AND TABLE_SCHEMA = 'dbo'
                        ORDER BY ORDINAL_POSITION
                    """
                    cursor.execute(query, table)
                
                result = cursor.fetchall()
                schema = {}
                for row in result:
                    schema[row[0]] = f"Type: {row[1]}, Max Length: {row[2]}, Nullable: {row[3]}, Default: {row[4]}"
                self.table_schemas[table] = schema
            
            cursor.close()
        except Exception as e:
            print(f"Error getting table descriptions: {e}")

    # ------------------------------------------------------------------ #
    #  Step 3 – Detect foreign key relationships from DB metadata
    # ------------------------------------------------------------------ #
    def _detect_foreign_keys(self):
        """Query database system catalogs for all FK constraints."""
        try:
            cursor = self.connection.cursor()
            
            if self.db_type == "postgresql":
                fk_query = """
                    SELECT
                        tc.table_name       AS source_table,
                        kcu.column_name     AS source_column,
                        ccu.table_name      AS target_table,
                        ccu.column_name     AS target_column
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = 'public';
                """
            else:  # sqlserver
                fk_query = """
                    SELECT 
                        OBJECT_NAME(fk.parent_object_id) AS source_table,
                        COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS source_column,
                        OBJECT_NAME(fk.referenced_object_id) AS target_table,
                        COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS target_column
                    FROM sys.foreign_keys AS fk
                    INNER JOIN sys.foreign_key_columns AS fkc 
                        ON fk.object_id = fkc.constraint_object_id
                    INNER JOIN sys.tables AS t 
                        ON fk.parent_object_id = t.object_id
                    WHERE SCHEMA_NAME(t.schema_id) = 'dbo'
                    ORDER BY source_table, source_column
                """
            
            cursor.execute(fk_query)
            rows = cursor.fetchall()

            for source_table, source_col, target_table, target_col in rows:
                self.table_relationships.setdefault(source_table, []).append({
                    "column": source_col,
                    "references_table": target_table,
                    "references_column": target_col,
                })

            cursor.close()
            print(f"Detected {sum(len(v) for v in self.table_relationships.values())} foreign key relationships from DB metadata")
        except Exception as e:
            print(f"Error detecting foreign keys: {e}")

    # ------------------------------------------------------------------ #
    #  Step 4 – Infer likely relationships by naming conventions
    #           (catches cases where FKs exist logically but aren't
    #            enforced as actual DB constraints)
    # ------------------------------------------------------------------ #
    def _infer_relationships(self):
        """Heuristic: if a column name matches <other_table>_id or <other_table>Id, treat it as a relationship."""
        all_tables = set(self.table_names)

        for table, schema in self.table_schemas.items():
            existing_fk_cols = {r["column"] for r in self.table_relationships.get(table, [])}

            for col_name in schema:
                if col_name in existing_fk_cols:
                    continue  # already have a real FK for this

                col_lower = col_name.lower().replace(" ", "_")

                # Pattern: column ends with _id or id, strip to get candidate table
                for suffix in ("_id", "id"):
                    if col_lower.endswith(suffix):
                        candidate = col_lower[: -len(suffix)].rstrip("_")
                        break
                else:
                    continue

                # Check if candidate matches any table name (singular or plural)
                for t in all_tables:
                    t_lower = t.lower()
                    if t == table:
                        continue
                    if candidate in (t_lower, t_lower.rstrip("s"), t_lower + "s"):
                        # Find the probable PK of the target table (id, <table>_id, Id)
                        target_cols = list(self.table_schemas.get(t, {}).keys())
                        target_pk = None
                        for tc in target_cols:
                            if tc.lower() in ("id", f"{t_lower}_id", f"{candidate}_id"):
                                target_pk = tc
                                break
                        if target_pk is None and target_cols:
                            target_pk = target_cols[0]  # fallback to first column

                        self.table_relationships.setdefault(table, []).append({
                            "column": col_name,
                            "references_table": t,
                            "references_column": target_pk,
                        })
                        print(f"  Inferred: {table}.{col_name} -> {t}.{target_pk}")
                        break

    # ------------------------------------------------------------------ #
    #  Main entry point
    # ------------------------------------------------------------------ #
    def generate_schema_description(self):
        try:
            self._getting_table_description()
            self._detect_foreign_keys()
            self._infer_relationships()

            agent = Agent(
                model=bedrock_model_custom,
                tools=[execute_query],
                system_prompt="""You are a specialist in generating descriptions for database table columns that help other agents write correct SQL.
                
Consider the table schema provided and use the attached tool to read sample data from the table if needed.

Guidelines:
- Consider neighboring columns before generating a column description.
- If relationship / foreign key info is provided, mention which table and column it references in the description.
- The table description should mention how this table relates to other tables in the database.
- Use the tool to read ROW values if needed before generating the description.""",
            )

            tables = []
            for table_name in self.table_schemas:
                print(f"Generating AI description for table: {table_name}")

                # Build the prompt including relationship context
                relationships = self.table_relationships.get(table_name, [])
                rel_text = ""
                if relationships:
                    rel_text = "\n\nKnown relationships (foreign keys):\n"
                    for r in relationships:
                        rel_text += f"  - {table_name}.{r['column']} -> {r['references_table']}.{r['references_column']}\n"

                human_message = (
                    f"Table name: {table_name}\n"
                    f"Columns: {json.dumps(self.table_schemas[table_name], indent=2)}"
                    f"{rel_text}"
                )

                result = agent.structured_output(output_model=TableSchema, prompt=human_message)
                print("agent invoked")

                table_data = result.model_dump()

                # Attach relationships to the output even if the AI didn't fill them
                if relationships:
                    table_data["relationships"] = relationships

                tables.append(table_data)

            # Write to a stable, known path
            with open(SCHEMA_OUTPUT_PATH, "w") as file:
                json.dump(tables, file, indent=2)

            print(f"✓ Successfully generated schema for {len(tables)} tables from {self.db_type} -> {SCHEMA_OUTPUT_PATH}")

        except Exception as e:
            print(f"Error generating schema: {e}")
        finally:
            if self.connection and not self.connection.closed:
                self.connection.close()
                print(f"{self.db_type} connection closed")