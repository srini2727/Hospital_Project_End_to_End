import pyodbc
import pandas as pd

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def load_dynamic_data_from_mssql(*args, **kwargs):
    # Gets the "ingredients" (variables) for this pipeline run
    source_database = kwargs.get('source_database')
    source_schema = kwargs.get('source_schema')
    source_table = kwargs.get('source_table')

    print(f"Loading data from: {source_database}.{source_schema}.{source_table}")

    # Dynamically builds the query using the variables
    query = f"SELECT * FROM [{source_database}].[{source_schema}].[{source_table}];"

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=host.docker.internal,1435;"
        f"DATABASE={source_database};"
        "UID=mage_user;"
        "PWD=mage_user;" # NOTE: Use a secure method for production
        "TrustServerCertificate=yes;"
    )

    cnxn = None
    try:
        cnxn = pyodbc.connect(connection_string)
        df = pd.read_sql(query, cnxn)
        print(f"Successfully loaded {len(df)} rows.")
        return df
    finally:
        if cnxn:
            cnxn.close()