import pyodbc
import pandas as pd
from mage_ai.io.snowflake import Snowflake
from pandas import Timestamp

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer

@transformer
def process_and_export_one_table(table_info: list, *args, **kwargs):
    """
    DYNAMIC BLOCK: Receives a list containing one dictionary with table info,
    loads its data, transforms it, and exports it to Snowflake.
    """
    # --- Get Info for this specific table ---
    # KEY CHANGE: The input is a list with one item. We get the dictionary at index 0.
    table_details = table_info[0]
    source_schema = table_details['TABLE_SCHEMA']
    source_table = table_details['TABLE_NAME']
    
    source_database = kwargs.get('source_database')
    print(f"--- Starting process for table: {source_database}.{source_schema}.{source_table} ---")

    # --- PART 1: LOAD DATA FROM MS SQL ---
    query = f"SELECT * FROM [{source_database}].[{source_schema}].[{source_table}];"
    connection_string_mssql = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=host.docker.internal,1435;"
        f"DATABASE={source_database};"
        "UID=mage_user;"
        "PWD=mage_user;" # Use your corrected, working password
        "TrustServerCertificate=yes;"
    )
    
    df = None
    try:
        with pyodbc.connect(connection_string_mssql) as cnxn_mssql:
            df = pd.read_sql(query, cnxn_mssql)
            print(f"Loaded {len(df)} rows from {source_table}.")
    except pyodbc.Error as e:
        print(f"ERROR loading data for {source_table}: {e}")
        raise
    
    # --- PART 2: TRANSFORM DATA ---
    df.columns = [col.upper() for col in df.columns]
    df['LOADED_AT_UTC'] = Timestamp.utcnow()

    # --- PART 3: EXPORT DATA TO SNOWFLAKE ---
    target_database = kwargs.get('target_database')
    target_schema = kwargs.get('target_schema')
    target_table = source_table 
    
    print(f"Exporting to Snowflake: {target_database}.{target_schema}.{target_table}")

    try:
        with Snowflake(
            account='vhystby-od93731',
            user='KOMMIREDDY5566',
            password='kommireddy5566', # YOU MUST ENTER YOUR SNOWFLAKE PASSWORD HERE
            warehouse='INGESTION_WH',
            database=target_database,
            schema=target_schema,
            role='SYSADMIN'
        ) as loader:
            loader.export(df, target_table, target_database, target_schema, if_exists='replace')
        
        print(f"--- Successfully exported {source_table}. ---")
        return {'status': 'success', 'table': source_table, 'rows_exported': len(df)}
        
    except Exception as e:
        print(f"ERROR exporting data for {target_table}: {e}")
        raise