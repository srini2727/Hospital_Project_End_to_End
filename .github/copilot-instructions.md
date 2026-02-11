# Hospital Analytics Codebase - AI Agent Instructions

## Project Overview

This is a **multi-source healthcare data pipeline** that integrates data from 3 hospital systems (H1, H2, H3) into a unified analytics warehouse using a **Medallion Architecture** (Bronze → Silver → Gold layers).

**Tech Stack:**
- **Orchestration:** Mage.ai (Python-based ELT pipelines)
- **Transformation:** dbt (Snowflake SQL)
- **Source:** MS SQL Server (3 hospital databases via ODBC)
- **Target:** Snowflake DW
- **Data Quality:** dbt tests + custom reconciliation macros

## Critical Architecture Pattern: The "Three Hospital" Design

**Key Insight:** This codebase handles **data from 3 separate hospital systems with inconsistent schemas**. This drives many design decisions:

1. **Staging Layer** (`hospital_staging/`): Creates separate models for each hospital's data (`stg_appointments_h1`, `stg_appointments_h2`, `stg_appointments_h3`)
2. **Silver Layer** (`hospital_silver/`): **Unifies all 3 sources** with complex logic to handle misaligned/shifted columns (see [appointments.sql](hospital_analytics/models/hospital_silver/appointments.sql) for pattern)
   - Uses `TRY_TO_DECIMAL()` to detect broken rows where columns shifted
   - Conditionally reconstructs data: `CASE WHEN TRY_TO_DECIMAL(suggestion) IS NOT NULL THEN suggestion...`
3. **Gold Layer** (`hospital_gold/`): Final analytics-ready views with business logic

**When adding new models:** Always follow this pattern—never skip the staging layer or attempt direct transformation.

## Data Flow & Pipeline Orchestration

### Master ELT Pipeline (`pipelines/master_elt_pipeline/metadata.yaml`)
The pipeline has two stages:
- **discovery_block** → **data_loader**: Discovers all tables in source database, then loads/exports them

**Connection Details (embedded in code):**
```
MSSQL: host.docker.internal:1435 (UID: mage_user)
Snowflake: vhystby-od93731 warehouse (credentials in exporters)
```

### Variables Pattern
Pipelines pass configuration via `kwargs`:
```python
source_database = kwargs.get('source_database')  # e.g., 'H1_hospital_data'
target_schema = kwargs.get('target_schema')      # e.g., 'HOSPITAL_BRONZE'
```
**Convention:** Always use `kwargs.get()` for pipeline variables; never hardcode.

### Data Loading & Export Pattern
See [final_run.py](data_exporters/final_run.py) for the canonical pattern:
1. **Discover** tables via `INFORMATION_SCHEMA.TABLES`
2. **Load** each table from MSSQL with `pd.read_sql()`
3. **Transform** (uppercase columns, add `LOADED_AT_UTC` timestamp)
4. **Export** to Snowflake with `Snowflake().export(..., if_exists='replace')`

## dbt Configuration & Layer Setup

**dbt Project:** `hospital_analytics/`

### Schema Naming Convention
- **HOSPITAL_BRONZE:** Raw source data (materialized as views in config, but actual tables from Mage)
- **HOSPITAL_STAGING:** Cleaned single-source data (views)
- **HOSPITAL_SILVER:** Unified multi-source data (tables for performance)
- **HOSPITAL_GOLD:** Analytics marts (views for real-time data)

**All objects are quoted** in dbt_project.yml for case-insensitivity:
```yaml
quoting:
  database: true
  schema: true
  identifier: true
```

### Staging Models Pattern
Each staging model covers ONE hospital source:
- File: `stg_{table}_h{1|2|3}.sql`
- Refs bronze source tables: `{{ ref('stg_appointments_h1') }}`
- Applies basic cleaning (column selection, null handling, type casting)

### Silver Model Pattern (Critical)
Silver models **ALWAYS combine 3 staging sources** with union logic:
```sql
WITH h1_data AS (SELECT ... FROM {{ ref('stg_appointments_h1') }})
, h2_data AS (SELECT ... FROM {{ ref('stg_appointments_h2') }})
, h3_data AS (SELECT ... FROM {{ ref('stg_appointments_h3') }})

SELECT * FROM h1_data
UNION ALL SELECT * FROM h2_data
UNION ALL SELECT * FROM h3_data
```

**Data Quality Issue:** Some tables have misaligned columns (e.g., `suggestion` field contains decimal values when a row is "broken"). Use conditional CASE statements to detect and realign:
```sql
CASE WHEN TRY_TO_DECIMAL(suggestion) IS NOT NULL THEN TRY_TO_DECIMAL(suggestion) ELSE fees END AS fees
```

### Gold Model Pattern
Gold models are **analytics-ready transformations**:
- Add business logic (e.g., ROW_NUMBER for fact keys)
- Format dates/times for reporting (e.g., `DAYNAME(appointment_date) || ', ' || TO_VARCHAR(...)`)
- Include computed columns (e.g., status icons as URLs)
- Join dimension tables for enrichment

**Naming:** Use `dim_` prefix for dimensions, `fct_` for facts.

## Data Quality & Testing

### Test Patterns
1. **Generic tests** (built-in dbt): `unique`, `not_null`, `relationships`
2. **Custom macro test** [test_row_count_reconciliation.sql](hospital_analytics/macros/test_row_count_reconciliation.sql):
   ```yaml
   tests:
     - row_count_reconciliation:
         parent_models: [ref('appointments')]
   ```
   Ensures row counts don't drop through layers (no data loss in transformations).

### Schema.yml Conventions
- Define sources in `schema.yml` for each layer (staging/silver/gold)
- Add `description` fields for documentation
- Use `config: {severity: warn}` for known data quality issues (e.g., duplicates in departments)

## Developer Workflows

### Running dbt
```bash
cd hospital_analytics/
dbt compile                          # Parse & validate
dbt run                             # Execute all models
dbt run --select models/hospital_gold  # Run only gold layer
dbt test                            # Run all tests
dbt docs generate && dbt docs serve # Generate documentation
```

### Running Mage Pipelines
Pipelines are defined in `pipelines/*/metadata.yaml`. Execution is via Mage UI or CLI.

### Adding a New Model
1. **Identify source table(s)** in MSSQL (check `source.yml`)
2. **Create staging model(s)**: `models/hospital_staging/stg_newtable_h{1|2|3}.sql`
3. **Create silver model** (if unifying multiple sources): `models/hospital_silver/newtable.sql` with UNION logic
4. **Create gold model** (if analytics use case): `models/hospital_gold/fact_or_dim_newtable.sql`
5. **Add tests** in `schema.yml` at each layer
6. **Run tests**: `dbt test`

### Debugging Patterns
- **Check Snowflake directly:** Query `HOSPITAL_BRONZE.{table}` to verify raw data
- **Check dbt run results:** Look in `hospital_analytics/target/run_results.json` for execution logs
- **Check dbt compiled SQL:** Review `hospital_analytics/target/compiled/` for actual SQL executed
- **Add `dbt logs`**: Set `debug: true` in `dbt_project.yml` for verbose output

## File Organization & Key Locations

| Directory | Purpose |
|-----------|---------|
| `data_loaders/` | Mage data loader blocks (source discovery, MSSQL extraction) |
| `data_exporters/` | Mage exporter blocks (Snowflake loading) |
| `transformers/` | Mage transformer blocks (data cleaning) |
| `hospital_analytics/models/` | dbt SQL transformation models |
| `hospital_analytics/macros/` | dbt custom macros (reconciliation tests) |
| `pipelines/master_elt_pipeline/` | Main orchestration config |

## Common Pitfalls & Solutions

| Issue | Solution |
|-------|----------|
| Column name case mismatches | Always uppercase in transformers; use quoted identifiers in dbt |
| Data loss in multi-source unification | Check row counts with `row_count_reconciliation` test |
| Connection string hardcoding | Use pipeline variables (`kwargs.get()`) or environment files |
| Missing `LOADED_AT_UTC` timestamps | Add in transformer before Snowflake export for audit trails |
| dbt model errors after Snowflake schema change | Run `dbt parse --defer-state` or rebuild target metadata |
| Broken column alignment from source systems | Use `TRY_TO_DECIMAL()` to detect shifted rows; conditionally reconstruct |

## External Dependencies & Credentials

**No hardcoded secrets should be committed.** Current issues:
- MSSQL credentials embedded in Python files (mage_user/mage_user)
- Snowflake credentials in exporters (KOMMIREDDY5566/kommireddy5566)

**Action:** Replace with environment variables or Mage secrets store before production.

## Extending the Codebase

### Adding a New Data Source (4th Hospital)
1. Update `source.yml` to include H4 tables
2. Create staging models `stg_*_h4.sql` for each table
3. Update silver models to include `h4_data` in UNION statements
4. Update dbt_project.yml if new schema needed
5. Test row counts match expectations

### Adding a New Analytics Mart (Gold Model)
1. Create `models/hospital_gold/{name}.sql`
2. Reference appropriate silver table(s) with `{{ ref('...') }}`
3. Add business logic: aggregations, window functions, formatting
4. Define tests in `schema.yml` (especially relationships to dimensions)
5. Run `dbt test` to validate

