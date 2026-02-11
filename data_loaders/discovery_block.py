# Block 1: The "Discovery" Data Loader
import pyodbc
import pandas as pd

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def discover_all_tables_in_db(*args, **kwargs):
    """
    Connects to a database defined by a pipeline variable, discovers all tables,
    and returns them as a simple list of dictionaries.
    """
    # Get the database name from the trigger you run
    database_to_scan = kwargs.get('source_database')
    
    print(f"--- Step 1: Discovering tables in database: {database_to_scan} ---")

    # This query gets the schema and name of all user tables in the database
    query = f"""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
      AND TABLE_CATALOG = '{database_to_scan}';
    """
    connection_string_mssql = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=host.docker.internal,1435;"
        f"DATABASE={database_to_scan};"
        "UID=mage_user;"
        "PWD=mage_user;" # Your working MS SQL password
        "TrustServerCertificate=yes;"
    )
    
    try:
        with pyodbc.connect(connection_string_mssql) as cnxn:
            list_of_tables_df = pd.read_sql(query, cnxn)
            print(f"Found {len(list_of_tables_df)} tables to process.")
            
            # This is the crucial part: convert the DataFrame to a list of dictionaries
            # This is the format Mage's "ForEach" loop needs.
            return list_of_tables_df.to_dict('records')
            
    except Exception as e:
        print(f"!!! ERROR: Could not discover tables in {database_to_scan}. {e}")
        raise