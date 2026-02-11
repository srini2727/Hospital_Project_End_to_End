from pandas import DataFrame
from mage_ai.io.snowflake import Snowflake

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def export_dynamic_data_to_snowflake(df: DataFrame, **kwargs) -> None:
    # Gets the "ingredients" (variables) for this pipeline run
    target_table = kwargs.get('source_table') # Use the source table name as the target
    target_schema = kwargs.get('target_schema')
    target_database = kwargs.get('target_database')

    print(f"Exporting {len(df)} rows to: {target_database}.{target_schema}.{target_table}")

    with Snowflake(
        account='vhystby-od93731',
        user='KOMMIREDDY5566',
        password='kommireddy5566', # NOTE: Use a secure method for production
        warehouse='INGESTION_WH',
        database=target_database,
        schema=target_schema
    ) as loader:
        loader.export(
            df,
            target_table,
            target_database,
            target_schema,
            if_exists='replace', # This will delete the old table and create a new one
        )
    print("Export complete.")
