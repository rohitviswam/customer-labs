# Work Log

## Entry 1 - Project Initialization (Day 0 - Nov 12, 2025)
**Time**: 2:00 PM - 3:30 PM  
**Duration**: 1.5 hours

### What I did:
- Read through the assignment requirements carefully
- Initialized git repository
- Created project folder structure (dbt_attribution, streaming, dashboard, docs, sketches)
- Drafted initial README with project overview and structure
- Researched GA4 public dataset schema in BigQuery

### Key decisions:
- Decided to use `bigquery-public-data.ga4_obfuscated_sample_ecommerce` as the primary dataset
- Chose Streamlit for dashboard (faster development, good for real-time updates)
- Planning to use Python BigQuery SDK for streaming pipeline

### Notes:
- Need to explore GA4 events schema tomorrow
- Should sketch out data flow architecture tonight
- Consider incremental models in dbt for performance

---

## Entry 2 - Architecture Design & Dataset Exploration (Day 0 - Evening)
**Time**: 8:00 PM - 10:00 PM  
**Duration**: 2 hours

### What I did:
- Created architecture diagram sketch (see sketches folder)
- Explored GA4 dataset structure in BigQuery console
- Documented key tables and fields for attribution
- Started drafting architecture.md

### Key findings:
- GA4 events are nested/repeated fields - need to flatten in staging
- Traffic source fields: `traffic_source.source`, `traffic_source.medium`, `traffic_source.name`
- User identification: `user_pseudo_id`, need to handle user_id if available
- Event timestamps are in microseconds

### Questions/Blockers:
- None yet - dataset is well documented

---

## Entry 3 - dbt Project Setup (Day 1 - Morning)
**Time**: [To be filled during actual work]  
**Duration**: [X hours]

### What I did:
- [Initialize dbt project with dbt-bigquery adapter]
- [Configure profiles.yml for BigQuery connection]
- [Set up dbt_project.yml with model configurations]
- [Create staging models for GA4 events]

### Challenges:
- [To be documented]

---

## Entry 4 - Staging Models & Tests (Day 1 - Afternoon)
**Time**: [To be filled]  
**Duration**: [X hours]

### What I did:
- [Build stg_ga4_events and stg_ga4_sessions]
- [Add schema.yml with column descriptions and tests]
- [Run initial dbt tests]

### Learnings:
- [To be documented]

---

## Entry 5 - Attribution Logic Implementation (Day 2 - Morning)
**Time**: [To be filled]  
**Duration**: [X hours]

### What I did:
- [Create intermediate models for touchpoint sequencing]
- [Implement first-click and last-click attribution logic]
- [Add lookback window logic (14 days)]

### Key decisions:
- [Document attribution tie-breaker logic]
- [Identity resolution strategy]

---

## Entry 6 - Streaming Pipeline Development (Day 2 - Afternoon)
**Time**: [To be filled]  
**Duration**: [X hours]

### What I did:
- [Create Python script for event streaming]
- [Implement deduplication using event_id]
- [Add latency tracking]
- [Test with sample events]

### Challenges:
- [Document any issues with BigQuery streaming API]

---

## Entry 7 - Dashboard Development (Day 2 - Evening / Day 3 - Morning)
**Time**: [To be filled]  
**Duration**: [X hours]

### What I did:
- [Build Streamlit dashboard with 4 key components]
- [Connect to BigQuery for real-time queries]
- [Add live event feed panel]
- [Create time series visualizations]

### Notes:
- [Document refresh rate and performance considerations]

---

## Entry 8 - Testing & Documentation (Day 3 - Afternoon)
**Time**: [To be filled]  
**Duration**: [X hours]

### What I did:
- [Run comprehensive dbt tests]
- [Test streaming pipeline end-to-end]
- [Document runbook and operational procedures]
- [Record demo video]

### Final checks:
- [List of items verified before submission]

---

## Summary

**Total Time**: [X] hours over 72-hour window  
**Key Learnings**: [To be filled at end]  
**Would Do Differently**: [Retrospective notes]

