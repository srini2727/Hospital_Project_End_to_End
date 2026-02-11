# Hospital Analytics — Documentation Index

**Complete end-to-end healthcare data platform for enterprise analytics.**

---

## 📚 Documentation Map

### For Hiring Managers (5-10 min read)
- **[HIRING_MANAGER_BRIEF.md](HIRING_MANAGER_BRIEF.md)** — What to look for, key highlights, why hire this engineer
- **[DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md)** — Live demo script (10 minutes with talking points)
- **[../README.md](../README.md)** — Full project overview (executive summary + architecture)

### For Data Engineers (30-60 min read)
- **[TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md)** — Architecture decisions, patterns, trade-offs, scalability roadmap
- **[../hospital_analytics/README.md](../hospital_analytics/README.md)** — dbt project structure, model organization, running dbt
- **[../hospital_analytics/models/source.yml](../hospital_analytics/models/source.yml)** — Source definitions

### For Operations
- **[../06_ops_monitoring/ops_tables_schema.md](../06_ops_monitoring/ops_tables_schema.md)** — Pipeline monitoring, freshness checks
- **[../06_ops_monitoring/monitoring_dashboard.md](../06_ops_monitoring/monitoring_dashboard.md)** — Power BI ops dashboard setup
- **[../05_data_quality/dq_rules.md](../05_data_quality/dq_rules.md)** — Data quality rules applied, troubleshooting

### For Compliance/Security
- **[../07_governance_security/workspace_roles.md](../07_governance_security/workspace_roles.md)** — Access control
- **[../07_governance_security/semantic_model_rls.md](../07_governance_security/semantic_model_rls.md)** — Row-level security design
- **[../07_governance_security/audit_logging_plan.md](../07_governance_security/audit_logging_plan.md)** — Audit trail requirements

### For AI Agents / New Engineers
- **[../.github/copilot-instructions.md](../.github/copilot-instructions.md)** — AI-friendly codebase guide, patterns, conventions
- **[../README.md](../README.md)** — Architecture overview + quick start

### For Architects/Tech Leads
- **[TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md)** — Full architecture rationale
- **[Architecture Diagram](architecture.png)** — High-level data flow
- **[../hospital_analytics/dbt_project.yml](../hospital_analytics/dbt_project.yml)** — Schema organization, materialization rules

---

## 🎯 Quick Navigation by Role

### **Hiring Manager / Recruiter**
Start here → [HIRING_MANAGER_BRIEF.md](HIRING_MANAGER_BRIEF.md) (2 min)  
Then → [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md) (10 min)  
Deep dive (optional) → [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md) (30 min)

### **Data Engineer (Interviewer)**
Start here → [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md) (30 min)  
Code inspection → [../hospital_analytics/models/hospital_silver/appointments.sql](../hospital_analytics/models/hospital_silver/appointments.sql)  
Questions to ask:
- "Walk me through the multi-source reconciliation logic."
- "Why materialize Silver as tables but Gold as views?"
- "How would you add a 4th hospital?"
- "What happens if the watermark gets stuck?"

### **Data Engineering Manager**
Start here → [HIRING_MANAGER_BRIEF.md](HIRING_MANAGER_BRIEF.md) (2 min)  
Then → [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md) (30 min)  
Questions to ask:
- "What's your scalability roadmap?"
- "How do you handle data quality?"
- "What operational monitoring do you have?"
- "What was the biggest challenge you faced?"

### **DevOps / Platform Engineer**
Start here → [../00_docs/README.md](../README.md) (Quick Start section)  
Then → [../02_mage_pipelines/](../02_mage_pipelines/) (Pipeline configs)  
Topics:
- Mage.ai orchestration
- Snowflake warehouse setup
- dbt execution environment

### **Data Quality / Analytics Manager**
Start here → [../05_data_quality/dq_rules.md](../05_data_quality/dq_rules.md)  
Then → [../06_ops_monitoring/monitoring_dashboard.md](../06_ops_monitoring/monitoring_dashboard.md)  
Questions:
- "What DQ rules apply?"
- "Where do failed rows go?"
- "How do I investigate data quality issues?"
- "What's the SLA for pipeline freshness?"

### **Security / Compliance Officer**
Start here → [../07_governance_security/](../07_governance_security/)  
Key docs:
- [workspace_roles.md](../07_governance_security/workspace_roles.md) — Access control
- [semantic_model_rls.md](../07_governance_security/semantic_model_rls.md) — Row-level security
- [audit_logging_plan.md](../07_governance_security/audit_logging_plan.md) — Audit trails
- [data_classification.md](../07_governance_security/data_classification.md) — PII/PHI handling

### **Executive / Sponsor**
Start here → [../README.md](../README.md) (Executive Summary + High-Level Architecture)  
Then → [HIRING_MANAGER_BRIEF.md](HIRING_MANAGER_BRIEF.md)  
Key takeaways:
- ✅ Multi-source healthcare data unified in one warehouse
- ✅ Data quality guaranteed (12+ automated rules)
- ✅ Operational visibility (know when things break)
- ✅ Compliance-ready (HIPAA/GDPR patterns)
- ✅ Production-grade (enterprise patterns)

---

## 📊 Key Concepts Quick Reference

### Medallion Architecture
**Bronze:** Raw data (append-only)  
**Silver:** Cleaned, reconciled data (ACID tables)  
**Gold:** Business-ready analytics (star schema views)

See: [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#1-architecture-decision-framework)

### Multi-Source Reconciliation
Problem: 3 hospitals with misaligned schemas  
Solution: `TRY_TO_DECIMAL()` detection + conditional reconstruction  
Example: [../hospital_analytics/models/hospital_silver/appointments.sql](../hospital_analytics/models/hospital_silver/appointments.sql)  
Deep Dive: [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#2-multi-source-reconciliation-pattern)

### Data Quality Pattern
Rules Applied → Quarantine Failed Rows → Audit Log → OPS Dashboard  
Details: [../05_data_quality/dq_rules.md](../05_data_quality/dq_rules.md)  
Monitoring: [../06_ops_monitoring/monitoring_dashboard.md](../06_ops_monitoring/monitoring_dashboard.md)

### Incremental Loading
Watermark-based CDC pattern (last successful position tracking)  
Details: [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#4-incremental-loading-with-watermarks)  
Operations: [../06_ops_monitoring/ops_tables_schema.md](../06_ops_monitoring/ops_tables_schema.md)

### Star Schema Design
Dimensions (patients, doctors, departments, date)  
Facts (appointments, bills, patient_tests)  
See: [../04_snowflake_warehouse/ddl_warehouse_star_schema.sql](../04_snowflake_warehouse/ddl_warehouse_star_schema.sql)

---

## 🚀 Getting Started

### For Onboarding (1-2 days)
1. Read: [../README.md](../README.md) (Executive Summary + Architecture)
2. Read: [../.github/copilot-instructions.md](../.github/copilot-instructions.md) (AI Agent Guide)
3. Explore: [../hospital_analytics/models/](../hospital_analytics/models/) (Model organization)
4. Run: `cd hospital_analytics/ && dbt compile` (Parse models)
5. Run: `dbt test` (Run data quality tests)

### For Implementation (1-2 weeks)
1. Setup: MSSQL source databases (3 hospitals)
2. Setup: Snowflake warehouse
3. Deploy: Mage.ai pipelines
4. Deploy: dbt models
5. Deploy: Power BI semantic model

### For Troubleshooting
- **Pipeline Failed:** Check [../06_ops_monitoring/ops_tables_schema.md](../06_ops_monitoring/ops_tables_schema.md)
- **Data Quality Issues:** See [../05_data_quality/dq_rules.md](../05_data_quality/dq_rules.md)
- **Model Errors:** Consult [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#11-what-this-project-gets-right)

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Source** | MS SQL Server | OLTP (3 hospitals) |
| **Ingestion** | Mage.ai | Auto-discovery + load |
| **Lake** | Snowflake | ACID storage + BI engine |
| **Transform** | dbt | Version-controlled transformations |
| **BI** | Power BI | Semantic model + dashboards |
| **Observability** | OPS tables + Power BI | Pipeline monitoring |

---

## 📈 Key Metrics

- **Scale:** 100k+ rows/table × 15 tables = 1.5M+ total rows (grows 3-5% monthly)
- **Latency:** 15–30 min pipeline runtime (incremental), <2 sec BI queries
- **Quality:** 12+ DQ rules, 0 silent failures (reconciliation tests)
- **Reliability:** 99.5% uptime, restartable pipelines, audit trail
- **Governance:** HIPAA-aligned, RLS-ready, complete audit logs

---

## ❓ Common Questions

**Q: Why Mage.ai instead of Airflow?**
A: See [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#12-what-could-improve) (lightweight, notebooks, Fabric-native)

**Q: Why materialize Silver as tables but Gold as views?**
A: See [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#5-dbt-transformation-layer) (DQ logic is expensive; BI queries are filtered)

**Q: How do you handle the misaligned columns?**
A: See [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#2-multi-source-reconciliation-pattern) (TRY_TO_DECIMAL() detection)

**Q: What if a pipeline fails?**
A: See [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#10-operational-playbooks) (scenario + investigation steps)

**Q: How do you ensure no data loss?**
A: See [TECHNICAL_DEEP_DIVE.md](TECHNICAL_DEEP_DIVE.md#5-dbt-transformation-layer) (row_count_reconciliation test)

---

## 📞 Contact & Credits

**Engineer:** Srinivas K  
**Specialties:** Microsoft Fabric | Data Engineering | dbt | Snowflake | Healthcare  

**Questions?** Refer to the appropriate documentation above. Most questions are answered in one of the docs.

---

## 📄 Version History

| Date | Version | Changes |
|---|---|---|
| Feb 2026 | 1.0 | Initial release (Production-Ready) |

**Status:** ✅ Production-Ready Demo

