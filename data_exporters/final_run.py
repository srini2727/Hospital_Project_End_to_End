import pyodbc
import pandas as pd
from mage_ai.io.snowflake import Snowflake
from pandas import Timestamp

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def load_and_export_all_tables(*args, **kwargs):
    """
    This single block does everything:
    1. Discovers all tables in a MS SQL database.
    2. Loops through each table.
    3. Loads the data for that table.
    4. Transforms it.
    5. Exports it to Snowflake.
    """
    # --- Configuration ---
    # You can change this to a pipeline variable later if you want
    source_database = 'H1_hospital_data' 
    target_database = 'HOSPITAL_DATA_DB'
    target_schema = 'HOSPITAL_BRONZE'
    
    # --- PART 1: DISCOVER ALL TABLES ---
    print(f"--- Step 1: Discovering tables in database: {source_database} ---")
    
    connection_string_mssql = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=host.docker.internal,1435;"
        f"DATABASE={source_database};"
        "UID=mage_user;"
        "PWD=mage_user;" # Use your corrected, working password
        "TrustServerCertificate=yes;"
    )

    list_of_tables = []
    try:
        with pyodbc.connect(connection_string_mssql) as cnxn:
            df_tables = pd.read_sql(f"SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_CATALOG = '{source_database}';", cnxn)
            list_of_tables = df_tables.to_dict('records')
            print(f"Found {len(list_of_tables)} tables to process.")
    except Exception as e:
        print(f"!!! ERROR: Could not discover tables. {e}")
        raise

    # --- PART 2: LOOP THROUGH EACH TABLE AND PROCESS ---
    print("\n--- Step 2: Starting to process each table ---")
    
    success_log = []
    error_log = []

    for i, table_info in enumerate(list_of_tables):
        source_schema = table_info['TABLE_SCHEMA']
        source_table = table_info['TABLE_NAME']
        
        print(f"\n--- Processing table {i+1}/{len(list_of_tables)}: {source_database}.{source_schema}.{source_table} ---")
        
        # Load data for this specific table
        try:
            with pyodbc.connect(connection_string_mssql) as cnxn_mssql:
                df = pd.read_sql(f"SELECT * FROM [{source_database}].[{source_schema}].[{source_table}];", cnxn_mssql)
                print(f"Loaded {len(df)} rows from {source_table}.")
        except Exception as e:
            print(f"!!! ERROR loading data for {source_table}: {e}")
            error_log.append({'table': source_table, 'error': str(e)})
            continue 

        # Transform data
        df.columns = [col.upper() for col in df.columns]
        df['LOADED_AT_UTC'] = Timestamp.utcnow()

        # Export data to Snowflake
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
            continue
            
    # --- PART 3: FINAL SUMMARY ---
    print("\n\n--- MIGRATION SUMMARY ---")
    print(f"Successfully processed {len(success_log)} tables.")
    print(f"Failed to process {len(error_log)} tables.")
    if error_log:
        print("Errors occurred on the following tables:")
        for error in error_log:
            print(f"- {error['table']}: {error['error']}")
            
    return success_log