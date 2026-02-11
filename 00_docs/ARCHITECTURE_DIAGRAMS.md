# 🏗️ Hospital Analytics — Architecture Diagrams

**Visual reference for understanding the data flow and system design.**

---

## 1️⃣ High-Level Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OPERATIONAL SOURCES (OLTP)                       │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  Hospital 1      │  │  Hospital 2      │  │  Hospital 3      │ │
│  │  MSSQL Server    │  │  MSSQL Server    │  │  MSSQL Server    │ │
│  │  (Patients,      │  │  (Same Schema,   │  │  (Same Schema,   │ │
│  │   Appointments,  │  │   Different Data)│  │   Different Data)│ │
│  │   Doctors, etc)  │  │                  │  │                  │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │
│           │                     │                     │             │
└───────────┼─────────────────────┼─────────────────────┼─────────────┘
            │ ODBC Connections    │                     │
            │ (host.docker.internal:1435)              │
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   MAGE.AI PIPELINE         │
                    │ (master_elt_pipeline)      │
                    │                            │
                    │ discovery_block:           │
                    │ Auto-discover all tables   │
                    │ using INFORMATION_SCHEMA   │
                    │                            │
                    │ data_loader:               │
                    │ Extract & load each table  │
                    │ Normalize columns          │
                    │ Add LOADED_AT_UTC          │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────────────┐
                    │    SNOWFLAKE WAREHOUSE             │
                    │    (vhystby-od93731)               │
                    │                                    │
                    │  HOSPITAL_DATA_DB                  │
                    │  ├─ HOSPITAL_BRONZE                │
                    │  │  └─ Raw, append-only tables     │
                    │  │     (patients_h1, orders_h1,    │
                    │  │      patients_h2, orders_h2,    │
                    │  │      patients_h3, orders_h3)    │
                    │  │                                 │
                    │  └─ [dbt transforms here]          │
                    │                                    │
                    └─────────────┬──────────────────────┘
                                  │
                    ┌─────────────▼──────────────────────┐
                    │  DBT TRANSFORMATION LAYERS         │
                    │                                    │
                    │  HOSPITAL_STAGING (views)          │
                    │  ├─ stg_patients_h1/h2/h3          │
                    │  ├─ stg_appointments_h1/h2/h3      │
                    │  └─ ... (single-source clean)      │
                    │                                    │
                    │  HOSPITAL_SILVER (tables)          │
                    │  ├─ patients (unified 3 sources)   │
                    │  ├─ appointments (reconciled)      │
                    │  ├─ *_quarantine (DQ failures)     │
                    │  └─ (multi-source validated)       │
                    │                                    │
                    │  HOSPITAL_GOLD (views)             │
                    │  ├─ dim_patients                   │
                    │  ├─ fct_appointments               │
                    │  └─ (analytics-ready star schema)  │
                    │                                    │
                    └─────────────┬──────────────────────┘
                                  │
                    ┌─────────────▼──────────────────────┐
                    │   POWER BI (Semantic Model)        │
                    │                                    │
                    │  Dashboards:                       │
                    │  ├─ Executive Overview (KPIs)      │
                    │  ├─ Appointment Analytics          │
                    │  ├─ Patient Insights               │
                    │  ├─ Payments Health                │
                    │  ├─ Returns & Refunds              │
                    │  ├─ Inventory Risk                 │
                    │  └─ Data Ops Monitor (freshness)   │
                    │                                    │
                    └────────────────────────────────────┘
```

---

## 2️⃣ Medallion Architecture (Bronze → Silver → Gold)

```
┌─────────────────────────────────────────────────────────────────┐
│                  SNOWFLAKE MEDALLION ARCHITECTURE               │
└─────────────────────────────────────────────────────────────────┘

LAYER 1: BRONZE (Raw Data - Append Only)
═════════════════════════════════════════════════════════════════
Purpose: Capture all transactional data, preserve history
Storage: Views (materialized)
Format: As-is from source systems

┌──────────────────────────────────────────────────────────┐
│  HOSPITAL_BRONZE Schema                                 │
├──────────────────────────────────────────────────────────┤
│  ├─ appointments_h1 (100,000 rows)                      │
│  ├─ appointments_h2 (95,000 rows)                       │
│  ├─ appointments_h3 (98,500 rows)                       │
│  ├─ patients_h1 (50,000 rows)                           │
│  ├─ patients_h2 (48,000 rows)                           │
│  ├─ patients_h3 (52,000 rows)                           │
│  ├─ doctors_h1, doctors_h2, doctors_h3                  │
│  ├─ departments_h1, departments_h2, departments_h3      │
│  ├─ ... (15+ tables × 3 hospitals = 45 tables)          │
│  │                                                      │
│  └─ LOADED_AT_UTC (audit timestamp added by Mage.ai)    │
│                                                          │
│  Characteristics:                                        │
│  ✓ Append-only (preserves history)                      │
│  ✓ No transformations applied                           │
│  ✓ Column names uppercase (normalized)                  │
│  ✓ Contains all rows (good + bad)                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓ [dbt transforms]


LAYER 2: SILVER (Cleaned, Reconciled Data)
═════════════════════════════════════════════════════════════════
Purpose: Apply DQ rules, unify multi-source, audit failures
Storage: Tables (materialized for performance)
Format: Reconciled (columns realigned, business logic applied)

┌──────────────────────────────────────────────────────────┐
│  HOSPITAL_SILVER Schema                                 │
├──────────────────────────────────────────────────────────┤
│  Clean Tables:                                           │
│  ├─ appointments (H1+H2+H3 unified, 293,500 rows)       │
│  │  ├─ Multi-source reconciliation applied              │
│  │  ├─ TRY_TO_DECIMAL() used to detect shifted columns  │
│  │  └─ All 3 hospitals → single appointments table      │
│  │                                                      │
│  ├─ patients (H1+H2+H3 unified, 150,000 rows)           │
│  ├─ doctors (H1+H2+H3 unified)                          │
│  ├─ ... (15 unified tables, one per entity)             │
│  │                                                      │
│  Quarantine Tables (Failed DQ Rows):                    │
│  ├─ appointments_quarantine (1,500 rows failed DQ)      │
│  ├─ patients_quarantine (200 rows failed DQ)            │
│  └─ ... (one quarantine table per entity)               │
│                                                          │
│  Audit Table:                                            │
│  └─ dq_issues (log of all failures)                     │
│     ├─ row_id, table_name, issue_type                   │
│     ├─ failed_rule_id, timestamp                        │
│     └─ (investigation_status: pending/investigated)     │
│                                                          │
│  Characteristics:                                        │
│  ✓ Unified (all 3 hospitals in one table)              │
│  ✓ Reconciled (misaligned columns fixed)               │
│  ✓ DQ-validated (12+ rules applied)                    │
│  ✓ Audit trail (all failures logged)                   │
│  ✓ Quarantined (bad rows preserved, not deleted)       │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓ [dbt transforms]


LAYER 3: GOLD (Analytics-Ready, BI-Optimized)
═════════════════════════════════════════════════════════════════
Purpose: Business intelligence (star schema, fast queries)
Storage: Views (for real-time BI access)
Format: Dimensional model (dims + facts)

┌──────────────────────────────────────────────────────────┐
│  HOSPITAL_GOLD Schema (Star Schema)                      │
├──────────────────────────────────────────────────────────┤
│  Dimensions (Descriptive):                               │
│  ├─ dim_patients (150,000 rows)                          │
│  │  └─ PatientID, Name, DOB, Segment, ActiveFlag       │
│  │                                                      │
│  ├─ dim_doctors (5,000 rows)                            │
│  │  └─ DoctorID, Name, Specialty, Department           │
│  │                                                      │
│  ├─ dim_departments (300 rows)                          │
│  │  └─ DepartmentID, DepartmentName, HospitalID        │
│  │                                                      │
│  ├─ dim_date (3,650 rows)                               │
│  │  └─ DateID, Year, Month, DayOfWeek, IsWeekend       │
│  │                                                      │
│  Facts (Measurable Events):                             │
│  ├─ fct_appointments (293,500 rows)                     │
│  │  └─ Qty, Amount, Status, DurationMinutes            │
│  │                                                      │
│  ├─ fct_hospital_bills (500,000 rows)                   │
│  │  └─ Amount, ServiceType, PaymentStatus              │
│  │                                                      │
│  └─ fct_patient_tests (1,000,000 rows)                  │
│     └─ TestID, Result, Status, CostAmount              │
│                                                          │
│  Characteristics:                                        │
│  ✓ Star schema (easy BI joins)                          │
│  ✓ Pre-joined dimensions (fast queries)                 │
│  ✓ Normalized (no duplication)                          │
│  ✓ Formatted for BI (dates, currency, etc)             │
│                                                          │
└──────────────────────────────────────────────────────────┘


DATA QUALITY FLOW
═════════════════════════════════════════════════════════════════

Bronze (100% of data)
  ├─ Good rows (95%): 293,500 → Silver
  └─ Bad rows (5%): 15,000 → Quarantine
           ↓
Silver (95% of Bronze)
  ├─ Validated rows (98%): 287,430 → Gold
  └─ Suspicious rows (2%): 6,070 → Quarantine
           ↓
Gold (98% of Silver)
  └─ Analytics-ready: 287,430 rows for BI
     └─ All guaranteed quality + auditable
```

---

## 3️⃣ Multi-Source Reconciliation Pattern

```
THE CHALLENGE: Misaligned Columns Across Hospitals
═════════════════════════════════════════════════════════════════

Hospital 1 Data (Correct):
┌────────────────────────────────────────────┐
│ appointment_id │ patient_id │ doctor_id │ fees │ payment_method │
├────────────────┼────────────┼───────────┼──────┼────────────────┤
│ 001            │ P001       │ D001      │ 150  │ Credit Card    │
│ 002            │ P002       │ D002      │ 200  │ Cash           │
└────────────────────────────────────────────┘

Hospital 2 Data (Columns Shifted - Legacy ETL Bug):
┌────────────────────────────────────────────┐
│ appointment_id │ patient_id │ doctor_id │ fees    │ payment_method │
├────────────────┼────────────┼───────────┼─────────┼────────────────┤
│ 501            │ P301       │ D301      │ 150.0   │ 200            │ ← SHIFTED!
│ 502            │ P302       │ D302      │ 175.50  │ 100            │ ← SHIFTED!
│                                          ↑ Contains decimals
│                                          but should be fee
│                                          payment_method has numbers
└────────────────────────────────────────────┘

Actual Hospital 2 Data Structure (misaligned):
  fees column contains: "150.0" (should be in payment_method)
  payment_method column contains: "200" (should be in fees)


THE SOLUTION: TRY_TO_DECIMAL() Detection + Reconstruction
═════════════════════════════════════════════════════════════════

Step 1: DETECT broken rows
   IF TRY_TO_DECIMAL(payment_method) IS NOT NULL
   THEN row is broken (payment_method contains a number, not text)
   ELSE row is fine

Step 2: RECONSTRUCT values
   FOR broken rows:
     - fees = TRY_TO_DECIMAL(payment_method) ← Take number from wrong column
     - payment_method = fees ← Use what's in fees

Step 3: RESULT
   Both H1 and H2 now have aligned columns:
   ├─ fees: 150, 175.50 (decimal values)
   └─ payment_method: "Credit Card", "Cash" (text values)

Step 4: UNION all 3 hospitals
   SELECT * FROM appointments_h1
   UNION ALL SELECT * FROM appointments_h2 (reconstructed)
   UNION ALL SELECT * FROM appointments_h3
   
   Result: Single unified appointments table with 293,500 rows
           All from different hospitals, now aligned


CODE PATTERN (in hospital_silver/appointments.sql)
═════════════════════════════════════════════════════════════════

CASE WHEN TRY_TO_DECIMAL(payment_method) IS NOT NULL 
  THEN TRY_TO_DECIMAL(payment_method)    ← H2: extract from wrong column
  ELSE fees                               ← H1, H3: use correct column
END AS fees,

CASE WHEN TRY_TO_DECIMAL(payment_method) IS NOT NULL 
  THEN fees                               ← H2: payment_method was in fees
  ELSE payment_method                     ← H1, H3: use correct column
END AS payment_method
```

---

## 4️⃣ Incremental Loading Pattern (Watermark-Based CDC)

```
INCREMENTAL LOAD FLOW
═════════════════════════════════════════════════════════════════

Day 1: Initial Full Load
┌─────────────────────────────────────────────────────────┐
│ mssql:appointments (100,000 rows)                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ SELECT * FROM appointments                          │ │
│ │ → Load ALL 100,000 rows to Snowflake                │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Update Watermark: last_loaded = 2026-02-11 23:59      │
└─────────────────────────────────────────────────────────┘

Day 2: Incremental Load (Only New/Changed Rows)
┌─────────────────────────────────────────────────────────┐
│ 1. GET last_watermark from ops_watermark table:        │
│    → last_loaded = 2026-02-11 23:59                    │
│                                                         │
│ 2. QUERY only new appointments:                         │
│    SELECT * FROM mssql:appointments                    │
│    WHERE modified_date > '2026-02-11 23:59'            │
│    → Result: 500 new/updated rows (1.5 hours of work) │
│                                                         │
│ 3. LOAD to Snowflake:                                  │
│    INSERT INTO snowflake:appointments (new 500 rows)   │
│    → Total now: 100,500 rows                           │
│                                                         │
│ 4. UPDATE watermark:                                    │
│    UPDATE ops_watermark                                │
│    SET last_watermark = MAX(modified_date from day 2)  │
│    → Ready for day 3                                   │
└─────────────────────────────────────────────────────────┘

EFFICIENCY GAINS
═════════════════════════════════════════════════════════════════

Full Load (Every Time):
  - Load 45 tables × 100,000 rows each = 4.5M rows
  - Time: 2 hours

Incremental Load (After Day 1):
  - Load 45 tables × 500 new rows each = 22.5K rows
  - Time: 15 minutes (1.5% of data, 87.5% faster!)

Over 30 Days:
  - Full load every day: 30 × 2 hours = 60 hours
  - Incremental after day 1: 1 × 2 hours + 29 × 15 min = 9.25 hours
  - Savings: 50.75 hours (85% faster!)


OPS WATERMARK TABLE
═════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────┐
│ ops_watermark                                        │
├─────────────────────┬──────────────────────────────┤
│ table_name          │ last_watermark_ts            │
├─────────────────────┼──────────────────────────────┤
│ appointments        │ 2026-02-11 23:59:47.000 UTC  │
│ patients            │ 2026-02-11 23:58:12.000 UTC  │
│ doctors             │ 2026-02-11 23:57:33.000 UTC  │
│ departments         │ 2026-02-11 23:56:55.000 UTC  │
│ ... (45 rows)       │ ...                          │
└─────────────────────┴──────────────────────────────┘

⚠️ Risk: If watermark gets stuck
   → Next run will skip new data (data loss!)

✓ Mitigation: Daily validation query
   SELECT COUNT(*) FROM appointments
   WHERE modified_date > last_watermark
   HAVING COUNT(*) = 0 → Alert if no new data when expected
```

---

## 5️⃣ Data Quality Processing Pipeline

```
DATA QUALITY ARCHITECTURE
═════════════════════════════════════════════════════════════════

Stage 1: INGESTION (Mage.ai)
┌────────────────────────────────────────────┐
│ Raw data from MSSQL                        │
│ ├─ Column names: UPPERCASE                 │
│ ├─ Add LOADED_AT_UTC timestamp             │
│ └─ Load to HOSPITAL_BRONZE                 │
│                                            │
│ Result: 100% of data preserved (append)    │
└────────────────────────────────────────────┘
                   ↓

Stage 2: VALIDATION (dbt + SQL)
┌────────────────────────────────────────────┐
│ Apply 12+ DQ Rules:                        │
│                                            │
│ ✓ Rule 1: Not null primary keys            │
│ ✓ Rule 2: Valid date ranges                │
│ ✓ Rule 3: No duplicates (natural key)      │
│ ✓ Rule 4: Referential integrity            │
│ ✓ Rule 5: Amount > 0                       │
│ ✓ Rule 6: Appointment duration > 0         │
│ ✓ Rule 7: Hospital ID in (H1, H2, H3)     │
│ ✓ Rule 8: Patient age within range         │
│ ✓ Rule 9: Status in allowed values         │
│ ✓ Rule 10: No extreme outliers             │
│ ✓ Rule 11: Cross-hospital consistency      │
│ ✓ Rule 12: Multi-source alignment fix      │
│                                            │
│ For each rule:                             │
│   IF row fails → quarantine                │
│   ELSE → silver table                      │
│                                            │
└────────────────────────────────────────────┘
                   ↓
        ┌─────────┴────────────┐
        ↓                      ↓

GOOD ROWS (95%)          BAD ROWS (5%)
↓                        ↓
SILVER_CLEAN             SILVER_*_QUARANTINE
(287,430 rows)           (15,000 rows)
                         
                         + DQ_ISSUES LOG
                         ├─ row_id
                         ├─ rule_id
                         ├─ issue_description
                         ├─ timestamp
                         └─ status (pending/investigated)

Stage 3: AGGREGATION (dbt Gold)
┌────────────────────────────────────────────┐
│ Create star schema from SILVER clean data  │
│ ├─ Dimensions (patients, doctors, depts)   │
│ ├─ Facts (appointments, bills, tests)      │
│ └─ Add business logic (formatting, etc)    │
│                                            │
│ Result: 287,430 analytics-ready rows       │
│         (100% guaranteed quality)          │
└────────────────────────────────────────────┘
                   ↓

Stage 4: CONSUMPTION (Power BI)
┌────────────────────────────────────────────┐
│ BI dashboards query GOLD layer             │
│ ├─ Sub-second response times               │
│ ├─ Pre-joined star schema                  │
│ └─ Governed metrics (semantic model)       │
│                                            │
│ Users see: Clean, trustworthy data         │
└────────────────────────────────────────────┘


RECONCILIATION TEST (Catch Silent Data Loss)
═════════════════════════════════════════════════════════════════

✓ dbt Test: row_count_reconciliation

Purpose: Ensure no data loss between layers

Logic:
  BRONZE count   = 100,000 (all rows)
  STAGING count  = 100,000 (same, just cleaned)
  SILVER count   = 95,000  (some failed DQ)
  GOLD count     = 95,000  (same as silver, just aggregated)
  
  IF SILVER count < STAGING count
  THEN ✗ TEST FAILS (data loss detected!)
  ELSE ✓ TEST PASSES

Benefit: Know IMMEDIATELY if a transformation drops data
         (vs. hours/days later when someone notices wrong numbers)
```

---

## 6️⃣ OPS Monitoring & Observability

```
OPERATIONAL MONITORING ARCHITECTURE
═════════════════════════════════════════════════════════════════

Real-Time Tracking (OPS Tables)
┌──────────────────────────────────────────────────────┐
│ ops_run_log                                          │
├────────────────┬──────────────────────────────────┤
│ notebook       │ discovery_block                  │
│ start_time     │ 2026-02-11 22:00:00 UTC         │
│ end_time       │ 2026-02-11 22:15:33 UTC         │
│ duration_min   │ 15.55                           │
│ status         │ SUCCESS                         │
│ row_count      │ 45 tables processed             │
│ errors         │ 0                               │
├────────────────┴──────────────────────────────────┤
│ [Similar rows for other notebooks...]             │
│ - data_loader (30 min)                            │
│ - transform (20 min)                              │
│ - export (15 min)                                 │
│ Total: ~1.5 hours to refresh all data            │
└──────────────────────────────────────────────────────┘

Power BI "Data Ops Monitor" Dashboard
┌──────────────────────────────────────────────────────┐
│ KPIs:                                               │
│ ┌────────────────────────────────────────────────┐ │
│ │ 📊 Pipelines Fresh: 45/45 (100%)              │ │
│ │    (All ran < 4 hours ago)                     │ │
│ │                                                │ │
│ │ 🚨 Quarantine Count: 15,000 rows              │ │
│ │    (5% of data, trending: stable)             │ │
│ │                                                │ │
│ │ ⏱️ Avg Duration: 1.5 hours                    │ │
│ │    (within SLA: < 2 hours)                    │ │
│ │                                                │ │
│ │ ❌ Errors Last 7 Days: 0                       │ │
│ │    (100% reliability)                         │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ Trends (7-Day View):                               │
│ ┌────────────────────────────────────────────────┐ │
│ │ Duration: 1.5h → 1.6h → 1.5h → 1.45h          │ │
│ │ (Stable, no degradation)                      │ │
│ │                                                │ │
│ │ Quarantine: 15k → 14.8k → 15k → 15.2k        │ │
│ │ (Normal variation, no spike)                  │ │
│ └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘

Alert Thresholds
┌──────────────────────────────────────────────────────┐
│ 🔴 RED: Pipeline last run > 4 hours ago             │
│    → Action: Check logs, restart if needed          │
│                                                     │
│ 🟠 ORANGE: Quarantine count > 10% of daily volume   │
│    → Action: Investigate new DQ failures            │
│                                                     │
│ 🟡 YELLOW: Duration > 2 hours                       │
│    → Action: Optimize, add parallelization          │
│                                                     │
│ 🟢 GREEN: All within SLA                            │
│    → Action: No action needed                       │
└──────────────────────────────────────────────────────┘
```

---

## 📚 Summary: What These Diagrams Show

| Diagram | What It Demonstrates |
|---|---|
| **Data Flow** | End-to-end integration (MSSQL → Snowflake → BI) |
| **Medallion Layers** | Clear separation (Bronze/Silver/Gold) + row counts |
| **Reconciliation** | How multi-source columns are fixed |
| **Watermarks** | Incremental loading efficiency (15 min vs. 2 hours) |
| **Data Quality** | Pipeline from ingestion → quarantine → analytics |
| **Observability** | How production is monitored in real-time |

**For Hiring Managers:** These diagrams show this isn't amateur work—it's enterprise architecture.

