# Real-time Attribution Dashboard

**Candidate Assessment Project for CustomerLabs**  
**Role**: Data Engineer  
**Timeline**: 72 hours

## Project Overview

This project implements a near-real-time marketing attribution pipeline using:
- **BigQuery**: Data warehouse with GA4 public dataset
- **dbt**: Data transformation and modeling
- **Streaming Pipeline**: Python-based event ingestion
- **Dashboard**: Real-time visualization of attribution metrics

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architecture diagram and design decisions.

### Data Flow
```
GA4 Events (BigQuery) → dbt Staging → dbt Intermediate → Attribution Marts → Dashboard
                ↑
        Streaming Pipeline (Real-time events)
```

## Project Structure

```
.
├── dbt_attribution/          # dbt project for data transformation
│   ├── models/
│   │   ├── staging/         # stg_ models
│   │   ├── intermediate/    # int_ models
│   │   └── marts/          # Final attribution models
│   ├── tests/
│   └── dbt_project.yml
├── streaming/               # Real-time event streaming pipeline
│   ├── stream_events.py
│   └── requirements.txt
├── dashboard/              # Dashboard application
│   ├── app.py
│   └── requirements.txt
├── docs/                   # Documentation
│   ├── architecture.md
│   ├── runbook.md
│   └── assumptions.md
└── sketches/              # Design sketches and notes
```

## Key Features

### 1. Attribution Models
- **First-Click Attribution**: Credits the first touchpoint in the customer journey
- **Last-Click Attribution**: Credits the last touchpoint before conversion

### 2. Data Pipeline
- **Staging Layer**: Clean and standardize GA4 events
- **Intermediate Layer**: User sessions and touchpoint sequencing
- **Marts Layer**: Attribution calculations with configurable lookback windows

### 3. Streaming Demo
- Ingests 5-20 sample events into BigQuery
- Demonstrates near-real-time materialization
- Implements deduplication and idempotency

### 4. Real-time Dashboard
- First vs Last attribution comparison
- 14-day time series trends
- Channel breakdown analysis
- Live event feed panel

## Quick Start

### Prerequisites
- Python 3.9+
- BigQuery access (or use public GA4 dataset)
- dbt installed (`pip install dbt-bigquery`)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd customer-labs
   ```

2. **Configure BigQuery credentials**
   ```bash
   # Set up Google Cloud credentials
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
   ```

3. **Install dependencies**
   ```bash
   # dbt dependencies
   cd dbt_attribution
   pip install -r requirements.txt
   
   # Streaming pipeline
   cd ../streaming
   pip install -r requirements.txt
   
   # Dashboard
   cd ../dashboard
   pip install -r requirements.txt
   ```

4. **Configure dbt**
   ```bash
   cd dbt_attribution
   # Edit profiles.yml with your BigQuery project details
   dbt debug  # Verify connection
   ```

5. **Run dbt models**
   ```bash
   dbt deps
   dbt seed
   dbt run
   dbt test
   ```

6. **Run streaming pipeline**
   ```bash
   cd ../streaming
   python stream_events.py
   ```

7. **Launch dashboard**
   ```bash
   cd ../dashboard
   python app.py
   ```

## Dataset Information

**GA4 Public Dataset**: `bigquery-public-data.ga4_obfuscated_sample_ecommerce`

This project uses the official GA4 sample dataset which includes:
- E-commerce events (page views, purchases, add to cart)
- User demographics and device information
- Traffic sources and campaign parameters

## Key Assumptions

See [docs/assumptions.md](docs/assumptions.md) for detailed documentation.

### Identity Resolution
- Uses `user_pseudo_id` as primary identifier
- Falls back to `ga_session_id` for anonymous sessions
- No cross-device tracking in initial version

### Attribution Window
- **Lookback period**: 14 days (configurable)
- **Tie-breaker**: Earliest timestamp for first-click, latest for last-click
- **Session timeout**: 30 minutes (GA4 default)

### Conversion Events
- Primary: `purchase` event
- Secondary: `begin_checkout`, `add_to_cart` (configurable)

## Testing

```bash
# Run dbt tests
cd dbt_attribution
dbt test

# Run Python tests
cd ../streaming
pytest tests/

# Validate streaming pipeline
python stream_events.py --test-mode
```

## Monitoring & Operations

See [docs/runbook.md](docs/runbook.md) for detailed operational procedures.

### Cost Estimates
- **BigQuery**: ~$5-10/month for this dataset size
- **Streaming**: ~$1-5/month depending on volume
- **Dashboard hosting**: Free (Streamlit Cloud) or $5-10/month

### Monitoring Recommendations
- dbt Cloud for pipeline monitoring
- BigQuery audit logs for query performance
- Application logs for streaming pipeline health
- Dashboard metrics for data freshness

## Demo

- **Video Demo**: [Link to screencast]
- **Live Dashboard**: [Link to hosted dashboard]
- **dbt Docs**: [Link to dbt documentation site]

## Deliverables Checklist

- [x] Architecture diagram (1-page)
- [x] dbt project with staging → intermediate → marts
- [x] First-Click and Last-Click attribution models
- [x] dbt tests and documentation
- [x] Streaming pipeline with deduplication
- [x] Real-time dashboard with 4 key views
- [x] README with run instructions
- [x] Runbook with failure handling and monitoring
- [x] worklog.md with development entries
- [x] Sketches and notes
- [x] Git commit history
- [x] Demo video or live walkthrough ready

## Contact

For questions or clarifications: [Your Email]

---

**Submission Date**: [Date]  
**Time Spent**: ~[X] hours over 72-hour window
