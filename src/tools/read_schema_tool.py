from strands import tool
import json

@tool
def read_schema_tool(table_name) -> str:
    """
    Reads the schema of a billing data table and returns a description of each column.

    Returns:
        A string describing the schema of the billing data table.
    """

    try:
        with open("src/tools/tables_schema.json", 'r') as file:
            data = json.load(file)
        
        for x in data:
            if x['table_name'] == table_name:
                return x['columns']
        
        return "Pass a valid table_name"
    
    except Exception as e:
        print(e)




@tool
def get_tables():
    """
    get the list of tables that are available to answer the user query
    """

    with open("src/tools/tables_schema.json", 'r') as file:
        data = json.load(file)
    
    table_name_with_desc = []
    for x in data:
        table_name_with_desc.append(
            {
                "table_name" :x['table_name'],
                "description":x['description']
            }
        )


    return table_name_with_desc
        

# print(read_schema_tool('cars'))