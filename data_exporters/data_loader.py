import pyodbc
import pandas as pd
from mage_ai.io.snowflake import Snowflake
from pandas import Timestamp

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def export_all_tables_sequentially(list_of_tables: list, *args, **kwargs):
    """
    Receives a LIST of tables to process.
    Loops through the list and processes each table one by one.
    """
    # Get the global pipeline variables
    source_database = kwargs.get('source_database')
    target_database = kwargs.get('target_database')
    target_schema = kwargs.get('target_schema')

    success_log = []
    error_log = []

    # --- THIS IS OUR "FOR EACH" LOOP ---
    for i, table_info in enumerate(list_of_tables):
        source_schema = table_info['TABLE_SCHEMA']
        source_table = table_info['TABLE_NAME']
        
        print(f"\n--- Starting process for table {i+1}/{len(list_of_tables)}: {source_database}.{source_schema}.{source_table} ---")

        # --- PART 1: LOAD DATA FROM MS SQL FOR ONE TABLE ---
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
        except Exception as e:
            print(f"!!! ERROR loading data for {source_table}: {e}")
            error_log.append({'table': source_table, 'error': str(e)})
            continue # Skip to the next table in the loop

        # --- PART 2: TRANSFORM DATA ---
        df.columns = [col.upper() for col in df.columns]
        df['LOADED_AT_UTC'] = Timestamp.utcnow()

        # --- PART 3: EXPORT DATA TO SNOWFLAKE ---
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
            success_log.append({'table': source_table, 'rows_exported': len(df)})
            
        except Exception as e:
            print(f"!!! ERROR exporting data for {target_table}: {e}")
            error_log.append({'table': source_table, 'error': str(e)})
            continue # Skip to the next table
            
    # --- Loop Finished ---
    print("\n\n--- PIPELINE RUN SUMMARY ---")
    print(f"Successfully processed {len(success_log)} tables.")
    print(f"Failed to process {len(error_log)} tables.")
    if error_log:
        print("Errors occurred on the following tables:")
        for error in error_log:
            print(f"- {error['table']}: {error['error']}")
            
    return success_log