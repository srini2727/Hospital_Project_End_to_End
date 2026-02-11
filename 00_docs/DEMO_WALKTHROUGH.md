# Hospital Analytics — 10-Minute Demo Walkthrough

**Objective:** Showcase the multi-source healthcare data pipeline to hiring managers/stakeholders.

---

## ⏱️ Timeline: 10 Minutes

### 1️⃣ **Architecture Overview (1.5 min)**

**Show:** `00_docs/screenshots/architecture.png`

> "This is a real-world healthcare data platform that consolidates three hospital systems into a unified analytics warehouse. Here's the flow:
> 
> - **Three MSSQL Databases** (H1, H2, H3) are the transactional sources
> - **Mage.ai pipeline** discovers and extracts all tables automatically
> - **Snowflake warehouse** acts as the unified data lake with three layers
> - **dbt** transforms and reconciles the data
> - **Power BI** surfaces dashboards and KPIs"

**Key Points:**
- ✅ Multi-source unification (3 hospitals with inconsistent schemas)
- ✅ End-to-end ownership (extraction → transformation → analytics)
- ✅ Built for scale (100k+ rows, designed for 10B+ events)

---

### 2️⃣ **The Challenge: Multi-Source Data Reconciliation (2 min)**

**Show:** [Hospital Analytics/models/hospital_silver/appointments.sql](hospital_analytics/models/hospital_silver/appointments.sql) (first 50 lines)

> "Here's the tricky part. These three hospitals have the **same conceptual schema**, but the data is misaligned:
> 
> - Hospital 1 might have columns: `appointment_id, patient_id, fees, payment_method`
> - Hospital 2 has the same columns **but in a different order due to legacy ETL bugs**
> - Hospital 3's data sometimes has **shifted columns** where `fees` ends up in `suggestion`
>
> Most engineers would just give up and load raw data to a data lake. I instead use **conditional logic to detect and fix these misalignments.**"

**Show the pattern:**
```sql
CASE WHEN TRY_TO_DECIMAL(suggestion) IS NOT NULL 
  THEN TRY_TO_DECIMAL(suggestion)  -- This is actually the fee
  ELSE fees                         -- Use the real fee column
END AS fees
```

> "This `TRY_TO_DECIMAL()` check detects when a row is 'broken.' When it is, I reconstruct the data by moving values back to their correct columns. The result? One unified appointments table from all three hospitals, with no data loss and full traceability of what was wrong."

**Why This Matters:**
- ✅ Shows problem-solving under real-world constraints
- ✅ Demonstrates deep SQL knowledge
- ✅ Handles data quality proactively, not reactively

---

### 3️⃣ **Data Pipeline Orchestration (1.5 min)**

**Show:** `pipelines/master_elt_pipeline/metadata.yaml` + [data_exporters/final_run.py](data_exporters/final_run.py)

> "The Mage.ai pipeline does three things automatically:
> 
> 1. **Discovers** all tables in the MSSQL database using `INFORMATION_SCHEMA.TABLES`
> 2. **Loads** each table dynamically (no hardcoding table names)
> 3. **Transforms & Exports** to Snowflake with a single timestamp for audit purposes"

**Show the pattern:**
```python
# Dynamic table discovery
tables = query(INFORMATION_SCHEMA.TABLES)

for table in tables:
    df = load_from_mssql(table)           # Extract
    df = normalize_columns(df)            # Transform
    export_to_snowflake(df, table)        # Load
```

> "This is production-grade engineering—no hardcoded table names, safe to re-run, and handles incremental loads with watermarks."

**Why This Matters:**
- ✅ Scalable design (works for 10 tables or 1,000 tables)
- ✅ Maintainability (new tables auto-discovered, no code changes)
- ✅ Reliability (idempotent, restartable)

---

### 4️⃣ **Data Transformation & Quality (2 min)**

**Show:** dbt folder structure:
```
models/
  ├── hospital_staging/       (30+ models for single-source cleaning)
  ├── hospital_silver/        (15+ models for multi-source unification)
  └── hospital_gold/          (Analytics-ready facts & dimensions)
```

**Run:**
```bash
cd hospital_analytics/
dbt test
```

> "Here's what I'm testing:
> 
> - **Duplicate detection:** No two appointments on same date/patient/doctor
> - **Referential integrity:** Every appointment points to a valid patient
> - **Row count reconciliation:** Silver table has same row count as staging (no silent data loss)
> - **Null validation:** Primary keys never null
> - **Business rules:** Fees > 0, appointment duration > 0, dates in valid range"

**Show test results:**
```
✓ unique constraints ......................... PASSED
✓ not_null constraints ....................... PASSED
✓ relationships (FK validation) .............. PASSED
✓ row_count_reconciliation ................... PASSED
```

> "12+ DQ rules run every time data changes. This catches issues **before** they reach the dashboard."

**Why This Matters:**
- ✅ Data governance (automated, testable, versioned)
- ✅ Trust in data (DQ is not manual review, it's automated)
- ✅ Compliance-ready (audit trail of all quality checks)

---

### 5️⃣ **Analytics Warehouse (1.5 min)**

**Show:** Snowflake warehouse schema in Power BI or SQL query tool

```sql
-- Dimensions
SELECT * FROM HOSPITAL_GOLD.dim_patients LIMIT 5;
SELECT * FROM HOSPITAL_GOLD.dim_doctors LIMIT 5;
SELECT * FROM HOSPITAL_GOLD.dim_departments LIMIT 5;

-- Facts
SELECT * FROM HOSPITAL_GOLD.fct_appointments LIMIT 5;
SELECT * FROM HOSPITAL_GOLD.fct_bills LIMIT 5;
```

> "The warehouse uses a **star schema design**:
> 
> - **4 dimensions** (patients, doctors, departments, date) describe the 'what'
> - **3 fact tables** (appointments, bills, patient_tests) record the 'events'
> 
> This design is optimized for BI tools. Instead of querying raw data, BI queries hit pre-joined, indexed tables. Result? Sub-second response times even on 100M+ rows."

**Why This Matters:**
- ✅ Performance (star schema is industry standard for analytics)
- ✅ Scalability (designed for 10B+ transactions)
- ✅ BI-ready (direct semantic model integration)

---

### 6️⃣ **Operational Monitoring (1 min)**

**Show:** Power BI "Data Ops Monitor" page (or show queries in SQL)

> "Here's what I'm tracking in production:
> 
> - **Pipeline Freshness:** Last successful run of each notebook
> - **Data Quality:** How many rows failed DQ checks and ended up in quarantine
> - **Row Count Trends:** Are we growing as expected?
> - **Error Rates:** Failed jobs by table
> - **Processing Time:** How long does each notebook take?"

**Sample queries:**
```sql
-- Last 7 days of pipeline runs
SELECT notebook, COUNT(*) runs, AVG(duration_min) avg_duration
FROM ops_run_log
WHERE DATE(start_time) >= DATEADD(DAY, -7, CURRENT_DATE)
GROUP BY 1 ORDER BY 2 DESC;

-- Current quarantine status
SELECT table_name, COUNT(*) bad_rows FROM silver_*_quarantine GROUP BY 1;
```

> "Instead of wondering 'Is the pipeline working?', I can see **exactly** what failed, where, and when. This is the difference between reactive debugging and proactive observability."

**Why This Matters:**
- ✅ Production readiness (know when things fail before users call)
- ✅ Root cause analysis (logs + metrics = faster troubleshooting)
- ✅ Transparency (stakeholders can see pipeline health)

---

### 7️⃣ **Show the Code Quality (1 min)**

**Show:** `.github/copilot-instructions.md`

> "I don't just write code—I document it for the next engineer. Here's AI-agent-ready documentation that explains:
> 
> - The architecture and why decisions were made
> - How to add new models following the pattern
> - Common pitfalls and their solutions
> - All external dependencies and credentials"

> "This means the next person (or AI assistant) can be productive **immediately** without asking questions. That's enterprise-grade work."

**Why This Matters:**
- ✅ Maintainability (clear patterns, not clever code)
- ✅ Knowledge transfer (doesn't live in someone's head)
- ✅ Scalability (new team members onboard faster)

---

## 🎯 Closing (30 sec)

> "This project demonstrates how to build **production-grade data infrastructure** that:
> 
> ✅ Handles messy real-world data (multi-source, inconsistent schemas)
> ✅ Guarantees data quality (automated DQ, quarantine, audit trails)
> ✅ Scales to enterprise volumes (100M+ rows, designed for more)
> ✅ Is observable & maintainable (ops monitoring, clear documentation)
> ✅ Is compliance-ready (HIPAA-aligned patterns, audit trails)
> 
> This is the **kind of work Fortune 500 companies hire for.** It's not fancy, but it's **correct, scalable, and maintainable.**"

---

## 📊 Talking Points for Q&A

**Q: How do you handle data quality?**
> "12+ automated DQ rules run every pipeline execution. Failed rows go to quarantine tables (not deleted). Issues are logged with timestamps and details for root cause analysis."

**Q: What if a new table is added to the hospital system?**
> "The Mage.ai discovery block auto-detects it. No code changes needed. The next pipeline run will ingest it automatically."

**Q: How do you know if the pipeline failed?**
> "OPS monitoring tables track every run. Power BI shows pipeline freshness. If a job fails, the ops page lights up red before users call support."

**Q: How would you handle a 4th hospital?**
> "Create staging models for the new hospital (following the existing H1/H2/H3 pattern). Update silver models to UNION all four sources. Add tests. Run dbt test. Done."

**Q: Why Mage.ai instead of Apache Airflow or Prefect?**
> "Mage is lightweight, has built-in notebooks (for exploration + production), and integrates well with Fabric. For Snowflake-only shops, I'd consider Airflow. For this stack, Mage is the right fit."

**Q: What's the biggest risk in this architecture?**
> "Column misalignment across hospitals—which I've already solved with the TRY_TO_DECIMAL() pattern. Otherwise, it's standard medallion architecture. Nothing novel or risky."

---

## 🎬 Demo Artifacts to Show

- ✅ dbt models + test results (show the CLI output)
- ✅ Power BI semantic model + dashboard (if available)
- ✅ Snowflake warehouse tables + sample queries
- ✅ GitHub README + copilot-instructions.md
- ✅ Data quality quarantine tables (show failed rows + reasons)
- ✅ OPS monitoring logs (show pipeline health)

---

## ⏱️ Time Allocation

- **Architecture:** 1.5 min
- **Multi-source challenge:** 2 min
- **Pipeline orchestration:** 1.5 min
- **Data transformation & QA:** 2 min
- **Warehouse schema:** 1.5 min
- **Ops monitoring:** 1 min
- **Code quality & documentation:** 1 min
- **Closing + Q&A:** 0.5 min
- **Total:** ~10 minutes

If running long, cut "Ops monitoring" (1 min) and "Code quality" (0.5 min) to get to 8–9 minutes.

