# Submission Checklist

Use this checklist before submitting your project to ensure all requirements are met.

## Required Deliverables

### 1. Architecture Documentation [Complete]
- [x] 1-page architecture document created (`docs/architecture.md`)
- [x] System diagram with data flow
- [x] All tools and technologies listed
- [x] Dataset and table names specified
- [x] Streaming pipeline design documented

### 2. dbt Project [Complete]
- [x] dbt project initialized (`dbt_attribution/`)
- [x] `dbt_project.yml` configured
- [x] `profiles.yml` template provided
- [x] Staging models (`stg_*`)
  - [x] `stg_ga4_events.sql`
  - [x] `stg_ga4_sessions.sql`
  - [x] `stg_ga4_conversions.sql`
- [x] Intermediate models (`int_*`)
  - [x] `int_touchpoints.sql`
  - [x] `int_user_journeys.sql`
- [x] Mart models (`mart_*`)
  - [x] `mart_first_click_attribution.sql`
  - [x] `mart_last_click_attribution.sql`
  - [x] `mart_attribution_comparison.sql`
- [x] Schema documentation (`schema.yml` files)
- [x] dbt tests configured
- [x] Attribution assumptions documented

### 3. Streaming Demo [Complete]
- [x] Streaming script created (`streaming/stream_events.py`)
- [x] Generates 5-20 sample events
- [x] Streams to BigQuery
- [x] Deduplication implemented (insertId + event_id)
- [x] Idempotency verified
- [x] Latency tracking included
- [x] Requirements.txt provided

### 4. Real-time Dashboard [Complete]
- [x] Dashboard application created (`dashboard/app.py`)
- [x] First vs Last attribution totals displayed
- [x] 14-day time series chart
- [x] Channel breakdown visualizations
- [x] Live event feed panel
- [x] Auto-refresh capability
- [x] Requirements.txt provided

### 5. Documentation [Complete]
- [x] README.md with project overview
- [x] SETUP.md with installation instructions
- [x] Runbook with operational procedures (`docs/runbook.md`)
- [x] Assumptions document (`docs/assumptions.md`)
- [x] Architecture documentation (`docs/architecture.md`)
- [x] Failure handling documented
- [x] Monitoring suggestions included
- [x] Cost estimates provided

### 6. Anti-AI & Authenticity Checks [In Progress]
- [x] Git repository initialized
- [x] Incremental commits (need more throughout development)
- [x] worklog.md created with entries
- [ ] 6-10 worklog entries completed (currently 2/10)
- [x] Design sketches/notes created (`sketches/DESIGN_NOTES.md`)
- [ ] 2+ actual hand-drawn sketches/photos (need physical sketches)
- [ ] Ready for live 10-15 min walkthrough
- [ ] Ready for 15-min live SQL edit

### 7. Demo Video/Recording [Pending]
- [ ] 5-8 minute screencast recorded
  - [ ] Show architecture
  - [ ] Run dbt models
  - [ ] Execute streaming pipeline
  - [ ] Display dashboard
  - [ ] Explain attribution logic
- Alternative: Be ready for live demo

## Testing Checklist

### dbt Tests
- [ ] Run `dbt debug` - connection successful
- [ ] Run `dbt run` - all models build
- [ ] Run `dbt test` - all tests pass
- [ ] Run `dbt docs generate` - documentation builds

### Streaming Pipeline
- [ ] Script runs without errors
- [ ] Events appear in BigQuery
- [ ] Deduplication works (run test with `--test-dedup`)
- [ ] Latency is < 10 seconds

### Dashboard
- [ ] Streamlit app launches
- [ ] All 4 sections display correctly
- [ ] Queries complete successfully
- [ ] Auto-refresh works
- [ ] Handles missing data gracefully

### End-to-End
- [ ] Fresh data flows through entire pipeline
- [ ] Attribution calculations are correct
- [ ] Dashboard updates with new events

## Pre-Submission Tasks

### Code Quality
- [x] All code properly formatted
- [x] Comments and docstrings added
- [x] SQL queries optimized
- [x] Error handling implemented
- [x] Requirements.txt files complete

### Documentation
- [x] README is comprehensive
- [x] All assumptions documented
- [x] Edge cases explained
- [x] Setup instructions tested
- [x] Runbook is complete

### Repository
- [ ] .gitignore configured
- [ ] Sensitive data excluded (credentials)
- [ ] All files committed
- [ ] Commit messages are descriptive
- [ ] Repository is clean

### Submission Package
- [ ] Repository pushed to GitHub/GitLab
- [ ] Repository URL ready
- [ ] Dashboard URL or video link ready
- [ ] 1-page summary prepared
- [ ] worklog.md finalized
- [ ] Sketches included or photographed

## Submission Email Template

```
To: jobs@customerlabs.co
Subject: Attribution Dashboard Take-Home - [Your Name]

Hi CustomerLabs Team,

Please find my submission for the Real-time Attribution Dashboard assessment:

Deliverables:
- Repository: [GitHub/GitLab URL]
- Dashboard: [Live URL or Demo Video Link]
- Documentation: See README.md in repository

Project Summary:
- Dataset: bigquery-public-data.ga4_obfuscated_sample_ecommerce
- Tools: BigQuery, dbt, Python, Streamlit
- Attribution Models: First-Click & Last-Click
- Lookback Window: 14 days
- Streaming: Real-time event ingestion with deduplication

Key Documents:
- Architecture: docs/architecture.md
- Runbook: docs/runbook.md
- Assumptions: docs/assumptions.md
- Worklog: worklog.md
- Sketches: sketches/ directory

Quick Start:
1. Configure BigQuery credentials
2. Run: dbt run
3. Stream events: python streaming/stream_events.py
4. Launch dashboard: streamlit run dashboard/app.py

Highlights:
- [Your key achievement 1]
- [Your key achievement 2]
- [Your key achievement 3]

Time Investment:
- Approximately [X] hours over 72-hour window
- Detailed breakdown in worklog.md

I'm available for a live walkthrough and SQL editing session at your convenience.

Best regards,
[Your Name]
[Your Contact Info]
```

## Final Quality Checks

- [ ] All links work
- [ ] Code runs on fresh environment
- [ ] Documentation is accurate
- [ ] No placeholder text remains
- [ ] All TODO items completed
- [ ] Submission email sent

## Scoring Self-Assessment

Rate yourself on each criterion (0-10):

| Criterion | Max Points | Self-Score | Notes |
|-----------|-----------|------------|-------|
| dbt & Modeling | 30 | __ | Staging, intermediate, marts complete? |
| Attribution Logic | 25 | __ | First/Last click accurate? |
| Streaming & Realtime | 20 | __ | Events stream successfully? |
| Dashboard UX & Realtime | 15 | __ | All 4 panels working? |
| Docs & Ops Readiness | 10 | __ | Runbook comprehensive? |
| **Total** | **100** | **__** | Target: ≥85 for excellent |

## Post-Submission

- [ ] Email sent to jobs@customerlabs.co
- [ ] Confirmation received
- [ ] Repository remains accessible
- [ ] Prepare for interview/walkthrough
- [ ] Review SQL for live editing session
- [ ] Be ready to explain design decisions

---

**Completion Date**: _____________  
**Submitted By**: _____________  
**Time Spent**: _______ hours

Good luck!
