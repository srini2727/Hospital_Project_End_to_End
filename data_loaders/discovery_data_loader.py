import pyodbc
import pandas as pd

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def discover_tables_in_db(*args, **kwargs):
    """
    Connects to a database and discovers all tables, returning them as a list of dictionaries.
    """
    database_to_scan = kwargs.get('source_database', 'hospital_1')
    print(f"Discovering tables in database: {database_to_scan}")

    query = f"""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
      AND TABLE_CATALOG = '{database_to_scan}';
    """
    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=host.docker.internal,1435;"
        f"DATABASE={database_to_scan};"
        "UID=mage_user;"
        "PWD=mage_user;" # Use your corrected, working password
        "TrustServerCertificate=yes;"
    )
    
    try:
        with pyodbc.connect(connection_string) as cnxn:
            list_of_tables_df = pd.read_sql(query, cnxn)
            print(f"Found {len(list_of_tables_df)} tables to process.")
            
            # KEY CHANGE: Convert the DataFrame to a list of dictionaries
            return list_of_tables_df.to_dict('records')
            
    except pyodbc.Error as e:
        print(f"ERROR discovering tables in {database_to_scan}: {e}")
        raise