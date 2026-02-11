# 🚀 Local Development Setup Guide

**Get the Hospital Analytics project running on your local machine.**

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [1. Clone & Setup](#1-clone--setup)
- [2. Configure Environment](#2-configure-environment)
- [3. Run Mage.ai Pipeline](#3-run-mageai-pipeline)
- [4. Run dbt Transformations](#4-run-dbt-transformations)
- [5. Verify Setup](#5-verify-setup)
- [Troubleshooting](#troubleshooting)
- [Common Commands](#common-commands)

---

## Prerequisites

Before starting, ensure you have installed:

### Required Software
- **Git** (v2.25+)
- **Python** (v3.9+) — Check: `python --version`
- **pip** (Python package manager) — Included with Python 3.9+
- **Docker** (optional but recommended) — For MSSQL/Snowflake connections
- **Visual Studio Code** (recommended)

### Required Access
- [ ] **MSSQL Server access** (3 hospital databases: H1, H2, H3)
  - Connection: `host.docker.internal:1435` (Docker) or `localhost:1435` (local)
  - Credentials: `mage_user` / `mage_user`
- [ ] **Snowflake account access** 
  - Account: `vhystby-od93731`
  - You need: username, password (or SSO token)
- [ ] **GitHub repository access** (if private)

### Verify Prerequisites

```bash
# Check Python
python --version  # Should be 3.9 or higher

# Check pip
pip --version

# Check Git
git --version

# Check Docker (optional)
docker --version
```

---

## 1. Clone & Setup

### Step 1a: Clone the Repository

```bash
# Navigate to where you want the project
cd ~/projects

# Clone the repository
git clone https://github.com/YOUR_USERNAME/hospital_project_updated.git
cd hospital_project_updated

# Verify you're in the right directory
pwd  # Should end with: .../hospital_project_updated
```

### Step 1b: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# On Windows Command Prompt:
venv\Scripts\activate.bat

# Verify activation (prompt should show (venv))
which python  # macOS/Linux
where python  # Windows
```

### Step 1c: Install Python Dependencies

```bash
# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Install Mage.ai
pip install mage-ai==0.9.71

# Install dbt for Snowflake
pip install dbt-snowflake==1.6.0

# Install data processing
pip install pandas==2.0.3
pip install pyodbc==4.0.38  # For MSSQL connections

# Install utilities
pip install python-dotenv==1.0.0  # For .env file loading
pip install pyyaml==6.0  # For YAML parsing

# Verify installations
mage --version
dbt --version
```

---

## 2. Configure Environment

### Step 2a: Create .env File from Template

```bash
# Copy the template
cp .env.template .env

# Edit .env with your actual credentials
# On macOS/Linux:
nano .env

# On Windows (VS Code):
code .env
```

### Step 2b: Fill in .env Values

Update the following sections in your `.env` file:

#### MSSQL Connections (all 3 hospitals)

```
MSSQL_HOST_H1=host.docker.internal  # or 127.0.0.1 if running locally
MSSQL_USERNAME_H1=mage_user
MSSQL_PASSWORD_H1=mage_user
MSSQL_DATABASE_H1=H1_hospital_data
# ... repeat for H2, H3
```

**For Docker users:** Use `host.docker.internal` to reference host machine
**For local dev:** Use `127.0.0.1` or `localhost`

#### Snowflake Connection

```
SNOWFLAKE_ACCOUNT=vhystby-od93731      # Your account ID
SNOWFLAKE_USER=your_email@company.com  # Your Snowflake username
SNOWFLAKE_PASSWORD=your_password       # Your Snowflake password
SNOWFLAKE_DATABASE=HOSPITAL_DATA_DB
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
```

**To find your Snowflake account ID:**
1. Log into Snowflake web UI
2. In bottom left, click profile icon → Account
3. Copy "Account locator" (e.g., `vhystby-od93731`)

#### dbt Configuration

```
DBT_PROFILES_DIR=~/.dbt/               # Standard location
DBT_TARGET=dev                         # Use dev profile for local
DBT_THREADS=4                          # Parallel execution threads
```

### Step 2c: Create dbt profiles.yml (Snowflake Connection)

```bash
# Create dbt config directory
mkdir -p ~/.dbt

# Create profiles.yml
nano ~/.dbt/profiles.yml
```

**Add this to `~/.dbt/profiles.yml`:**

```yaml
hospital_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: vhystby-od93731
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      database: HOSPITAL_DATA_DB
      warehouse: COMPUTE_WH
      schema: HOSPITAL_STAGING
      threads: 4
      client_session_keep_alive: false
```

**Verify dbt connection:**

```bash
cd hospital_analytics/
dbt debug

# Should output: "All checks passed!"
```

---

## 3. Run Mage.ai Pipeline

### Step 3a: Start Mage.ai Server

```bash
# Load environment variables and start Mage
mage start hospital_analytics_pipeline

# Server will start at http://localhost:6789
```

### Step 3b: Access Mage.ai UI

1. Open browser: `http://localhost:6789`
2. Click on **Pipelines** (left sidebar)
3. Select **master_elt_pipeline**
4. Click **Run pipeline** button (top right)

**Expected behavior:**
- **discovery_block** runs first (5-10 min) — discovers all tables in MSSQL
- **data_loader** runs second (30-45 min) — extracts and loads to Snowflake Bronze
- **Status**: Should show "Pipeline run succeeded" when complete

### Step 3c: Verify Mage Pipeline Execution

```bash
# In Mage UI:
# 1. Click "master_elt_pipeline" in left sidebar
# 2. View "Runs" tab to see execution history
# 3. Click on a successful run to see logs
# 4. Should see: "FINISHED ... SUCCESS"

# Or check logs in terminal for errors
# If error: Check .env variables, MSSQL connectivity, Snowflake credentials
```

---

## 4. Run dbt Transformations

### Step 4a: Verify dbt Project

```bash
# Navigate to dbt project
cd hospital_analytics

# Parse and validate dbt models (no execution)
dbt parse

# Should output: "Completed successfully"
```

### Step 4b: Run dbt Bronze Layer (creates staging models)

```bash
# Run only staging models (Bronze layer)
dbt run --select models/hospital_staging

# Expected: ~30 staging models compiled and executed
# Time: 5-10 minutes
```

### Step 4c: Run dbt Silver Layer (multi-source unification)

```bash
# Run Silver layer (where multi-source reconciliation happens)
dbt run --select models/hospital_silver

# Expected: ~15 silver models compiled
# This is where the "three hospital" pattern is applied
# Time: 10-15 minutes
```

### Step 4d: Run dbt Gold Layer (analytics mart)

```bash
# Run Gold layer (BI-ready star schema)
dbt run --select models/hospital_gold

# Expected: 4 dimensions + 3 facts models compiled
# Time: 5 minutes
```

### Step 4e: Run All dbt Tests

```bash
# Execute all dbt tests (data quality checks)
dbt test

# Expected output:
# ✓ tests/unique_id.sql (passes)
# ✓ tests/not_null_id.sql (passes)
# ✓ tests/row_count_reconciliation (passes) ← Custom macro!
# ... more tests

# Time: 5-10 minutes
```

**What the tests check:**
- No duplicate primary keys (uniqueness)
- No null values in required fields (NOT NULL)
- Referential integrity (FK → PK matches)
- Row count doesn't drop between layers (our custom macro)

---

## 5. Verify Setup

### 5a: Check Snowflake Schemas Were Created

```bash
# In dbt project root
dbt docs generate  # This creates documentation

# Then open the docs:
dbt docs serve
# Browser will open to http://localhost:8000
# You should see the data lineage graph showing all layers
```

### 5b: Query Snowflake Directly (Optional)

Connect to Snowflake directly and verify data:

```bash
# Using SnowSQL CLI (if installed):
snowsql -a vhystby-od93731 -u your_user -d HOSPITAL_DATA_DB

# Once connected:
USE DATABASE HOSPITAL_DATA_DB;

-- Check Bronze layer (raw data)
SELECT COUNT(*) FROM HOSPITAL_BRONZE.appointments_h1;
-- Should return row count > 0

-- Check Silver layer (cleaned, unified)
SELECT COUNT(*) FROM HOSPITAL_SILVER.appointments;
-- Should return row count = sum of H1+H2+H3

-- Check Gold layer (analytics-ready)
SELECT COUNT(*) FROM HOSPITAL_GOLD.fct_appointments;
-- Should return row count for BI queries
```

### 5c: Check Power BI Connections (Optional)

If you have Power BI Desktop:

1. Open Power BI Desktop
2. **Get Data** → **Snowflake**
3. Connect to `vhystby-od93731` account
4. Select `HOSPITAL_GOLD` schema
5. Load the star schema (dimensions + facts)
6. Create a test visualization

---

## Troubleshooting

### ❌ Mage.ai Won't Start

**Error:** `Port 6789 already in use`

```bash
# Solution: Kill existing process and restart
# On macOS/Linux:
lsof -i :6789  # Shows process ID
kill -9 <PID>

# On Windows PowerShell:
Get-Process -Id (Get-NetTCPConnection -LocalPort 6789).OwningProcess | Stop-Process

# Then restart:
mage start hospital_analytics_pipeline
```

---

### ❌ MSSQL Connection Fails

**Error:** `Login failed for user 'mage_user'`

**Checklist:**
1. Verify MSSQL is running
   ```bash
   # Test connection (replace host based on Docker vs local)
   # Using sqlcmd (if SQL Server tools installed)
   sqlcmd -S host.docker.internal,1435 -U mage_user -P mage_user
   ```

2. Check `.env` has correct hostname:
   - Docker users: `host.docker.internal`
   - Local users: `127.0.0.1` or `localhost`

3. Verify database names in `.env`:
   - H1: `H1_hospital_data`
   - H2: `H2_hospital_data`
   - H3: `H3_hospital_data`

---

### ❌ Snowflake Connection Fails

**Error:** `Unable to connect to snowflake`

**Checklist:**
1. Verify account ID: `vhystby-od93731`
2. Verify username (email): `your_email@company.com`
3. Verify warehouse exists and you have access:
   ```bash
   dbt debug  # Run in hospital_analytics/ directory
   ```
4. Check profiles.yml is in `~/.dbt/profiles.yml`
5. Verify environment variables are loaded:
   ```bash
   echo $SNOWFLAKE_USER  # Should print your username
   ```

---

### ❌ dbt Models Fail

**Error:** `dbt run` fails with SQL compilation error

**Debug steps:**
```bash
# 1. Check compiled SQL
ls hospital_analytics/target/compiled/

# 2. Look at compiled SQL to find error
cat hospital_analytics/target/compiled/hospital_analytics/models/hospital_silver/appointments.sql

# 3. Run specific model with debug
dbt run --select appointments --debug

# 4. Check dbt.log for detailed errors
cat hospital_analytics/dbt.log
```

---

### ❌ Data Not Appearing in Snowflake

**Error:** Tables created but no data loaded

**Checklist:**
1. Check Mage.ai pipeline ran successfully:
   ```bash
   # In Mage UI: master_elt_pipeline → Runs tab
   # Should see "Pipeline run succeeded"
   ```

2. Check Bronze layer has data:
   ```sql
   SELECT COUNT(*) FROM HOSPITAL_BRONZE.appointments_h1;
   ```

3. Check for errors in dbt:
   ```bash
   dbt test  # Run quality tests to identify issues
   ```

4. Check quarantine tables for failed rows:
   ```sql
   SELECT * FROM HOSPITAL_SILVER.appointments_quarantine LIMIT 10;
   ```

---

## Common Commands

### Development Workflow

```bash
# 1. Make sure venv is activated
source venv/bin/activate  # macOS/Linux

# 2. Start Mage server
mage start hospital_analytics_pipeline

# 3. In another terminal, run dbt
cd hospital_analytics
dbt run

# 4. Test data quality
dbt test

# 5. Generate documentation
dbt docs generate && dbt docs serve

# 6. View lineage (opens at localhost:8000)
# Browser automatically opens
```

### Quick dbt Commands

```bash
# Compile all models (check for SQL errors)
dbt compile

# Run specific layer
dbt run --select models/hospital_silver

# Run specific model
dbt run --select appointments

# Run only tests
dbt test --select appointments

# Run tests for specific node
dbt test --select patient_tests_fact

# Dry run (show what would run without executing)
dbt run --select models/hospital_gold --dry-run

# Clean previous run artifacts
dbt clean
```

### Mage.ai Commands

```bash
# Start server
mage start hospital_analytics_pipeline

# Start with custom port
mage start hospital_analytics_pipeline --port 7000

# Run pipeline from CLI (without UI)
mage run hospital_analytics_pipeline master_elt_pipeline

# List all pipelines
mage list-pipelines
```

### Debugging

```bash
# Check Python virtual environment
which python  # macOS/Linux
where python  # Windows

# Verify all packages installed
pip list | grep -E "mage|dbt|pandas|pyodbc"

# Check environment variables
echo $SNOWFLAKE_USER
echo $MSSQL_HOST_H1

# Clear dbt cache and rebuild
dbt clean && dbt compile && dbt run
```

---

## Production Checklist

Before deploying to production:

- [ ] All tests pass: `dbt test`
- [ ] Row counts validated: Check row_count_reconciliation test passes
- [ ] Snowflake permissions set: Users can read Gold schema
- [ ] Credentials stored securely: Never commit .env to Git
- [ ] Monitoring alerts configured: Check ops_run_log for failed runs
- [ ] Documentation complete: `dbt docs` generated and reviewed
- [ ] Backup strategy in place: Snowflake snapshots configured
- [ ] Performance tuned: Run times meet SLA (< 2 hours full refresh)

---

## Next Steps

1. **Explore dbt Lineage:**
   ```bash
   dbt docs generate && dbt docs serve
   # Open localhost:8000 to see data flow from Bronze → Silver → Gold
   ```

2. **Run Demo Presentation:**
   - See [DEMO_WALKTHROUGH.md](../00_docs/DEMO_WALKTHROUGH.md)
   - Use this setup to walk through the data pipeline live

3. **Make Your First Change:**
   - Edit a dbt model in `hospital_analytics/models/`
   - Run `dbt run` to test
   - See changes in Snowflake instantly

4. **For Interview Prep:**
   - Run the full pipeline (Mage → dbt)
   - Be ready to explain each layer
   - Understand the multi-source reconciliation pattern (the key differentiator!)

---

## Support

If stuck, refer to:
- **Mage.ai docs:** https://docs.mage.ai/
- **dbt docs:** https://docs.getdbt.com/
- **Snowflake docs:** https://docs.snowflake.com/
- **This project's `.github/copilot-instructions.md`** for architecture patterns

Happy coding! 🚀

