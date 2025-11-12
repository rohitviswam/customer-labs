# Real-time Attribution Dashboard

**Candidate Assessment Project for CustomerLabs**  
**Role**: Data Engineer  
**Timeline**: 72 hours

> **⚠️ BigQuery Free Tier Note**: This implementation uses BigQuery views instead of tables/incremental models due to free tier limitations (no DML operations). The streaming pipeline is documented but requires a billing-enabled project to run. All attribution logic and dbt models are fully functional using the GA4 public dataset.

## Project Overview

This project implements a near-real-time marketing attribution pipeline using:
- **BigQuery**: Data warehouse with GA4 public dataset
- **dbt**: Data transformation and modeling
- **Streaming Pipeline**: Python-based event ingestion (requires billing-enabled project)
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

### 4. Interactive Dashboard (Streamlit)
The dashboard provides real-time visualization of attribution metrics with four key sections:

**1. Attribution Model Comparison**
- Side-by-side metrics for First-Click vs Last-Click attribution
- Total conversions and revenue comparison
- Delta calculations showing differences between models

**2. Attribution Trends (14-Day Time Series)**
- Daily conversion trends for both attribution models
- Revenue trends over time
- Interactive Plotly charts with hover details

**3. Channel Performance Breakdown**
- Conversion comparison by marketing channel
- Revenue breakdown by channel
- Visual comparison of First-Click vs Last-Click attribution per channel

**4. Live Event Feed**
- Real-time display of most recent events
- Event details including user ID, event type, and traffic source
- Timestamp with seconds-ago indicator

**Dashboard Features:**
- Auto-refresh capability for near real-time updates
- Configurable BigQuery project and dataset via sidebar
- Cached queries for optimal performance
- Responsive design that works on all screen sizes
- Direct connection to BigQuery attribution mart models

**Access:**
```bash
cd dashboard
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
streamlit run app.py
# Dashboard will open at http://localhost:8501
```

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
   dbt run
   dbt test
   ```

6. **Launch dashboard**
   ```bash
   cd dashboard
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
   streamlit run app.py
   # Access at http://localhost:8501
   ```

   **Dashboard Configuration:**
   - The dashboard automatically connects to your BigQuery project
   - Default dataset is pre-configured to `attribution_dev_marts`
   - You can modify project ID and dataset in the sidebar if needed
   - Enable auto-refresh for near real-time updates (refreshes every 10 seconds)

> **Note on Streaming Pipeline**: The streaming script (`streaming/stream_events.py`) requires BigQuery's streaming insert API, which is not available in the free tier. The dashboard and attribution models work perfectly with the existing GA4 public dataset without needing the streaming component.

## Dataset Information

**GA4 Public Dataset**: `bigquery-public-data.ga4_obfuscated_sample_ecommerce`

This project uses the official GA4 sample dataset (Nov 2020 - Jan 2021) which includes:
- **4.3 million events** across 3 months of data
- **44,449 conversions** (purchase, begin_checkout events)
- **360K+ unique touchpoints** deduplicated by user-channel-date
- **94K+ user journeys** with attribution analysis

**Data Coverage:**
- E-commerce events (page views, purchases, add to cart, begin checkout)
- User demographics and device information
- Traffic sources and campaign parameters (Direct, Organic Search, Paid Search, Referral, Social, Email)
- Geographic data (country, region, city)

**Dashboard Metrics (from dataset):**
- **Total Conversions**: 44,449
- **Active Channels**: Direct, Organic Search, Paid Search, Referral, Social, Email, Affiliate
- **Date Range**: November 2020 - January 2021
- **Attribution Window**: 14 days lookback

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

### Live Dashboard
The Streamlit dashboard is fully functional and displays:
- **44,449 total conversions** from the GA4 public dataset
- **Real-time comparison** of First-Click vs Last-Click attribution
- **14-day time series** showing conversion trends (Jan 17-31, 2021)
- **Channel breakdown** with 5+ marketing channels
- **Live event feed** showing most recent 20 events

**Sample Insights from Dashboard:**
- Direct traffic accounts for ~40% of conversions
- Organic Search contributes ~20-25% of conversions
- Last-Click model typically shows higher attribution than First-Click for Direct traffic
- Average daily conversions: ~300-400 across all channels

### Documentation
- **Architecture Diagram**: See `docs/architecture.md`
- **Operational Runbook**: See `docs/runbook.md`
- **Technical Assumptions**: See `docs/assumptions.md`
- **dbt Documentation**: Generate with `dbt docs generate && dbt docs serve`

### Video Walkthrough
[Link to screencast/demo video - to be added]

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

For questions or clarifications: rohitviswam@gmail.com

---

**Submission Date**: 12-11-2025  
