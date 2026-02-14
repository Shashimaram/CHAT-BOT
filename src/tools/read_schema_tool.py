from pathlib import Path
from langchain_core.tools import tool
import json

SCHEMA_PATH = Path(__file__).parent.parent / "tables_schema.json"

# Module-level cache – loaded once on first access, stays in memory.
_schema_cache: list | None = None


def _load_schema() -> list:
    """Return the cached schema list, reading from disk only on first call."""
    global _schema_cache
    if _schema_cache is None:
        with open(SCHEMA_PATH, "r") as file:
            _schema_cache = json.load(file)
    return _schema_cache


@tool
def read_schema_tool(table_name: str) -> str:
    """
    Reads the schema of a specific table and returns its columns and relationships.

    Args:
        table_name: Name of the table to look up.

    Returns:
        A dict with 'columns' and 'relationships' for the table, or an error message.
    """
    try:
        data = _load_schema()

        for table in data:
            if table["table_name"] == table_name:
                result = {"columns": table["columns"]}
                if table.get("relationships"):
                    result["relationships"] = table["relationships"]
                return json.dumps(result)

        available = [t["table_name"] for t in data]
        return f"Table '{table_name}' not found. Available tables: {available}"

    except Exception as e:
        return f"Error reading schema: {e}"


@tool
def get_tables() -> str:
    """
    Get a lightweight list of tables in the database: name, description,
    column names (just names, not full details), and foreign-key relationships.
    Use read_schema_tool to get full column details for a specific table.
    """
    try:
        data = _load_schema()

        tables_summary = []
        for table in data:
            entry = {
                "table_name": table["table_name"],
                "description": table["description"],
                "columns": [c["column_name"] for c in table.get("columns", [])],
            }
            if table.get("relationships"):
                entry["relationships"] = table["relationships"]
            tables_summary.append(entry)

        return json.dumps(tables_summary)

    except Exception as e:
        return f"Error loading tables: {e}"

