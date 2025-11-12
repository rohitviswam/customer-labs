# Architecture Documentation

## System Overview

This document outlines the architecture for a near-real-time marketing attribution pipeline that computes First-Click and Last-Click attribution models using GA4 data.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────┤
│  GA4 Public Dataset                    Real-time Events          │
│  bigquery-public-data.                 (Streaming Pipeline)      │
│  ga4_obfuscated_sample_ecommerce                                │
└──────────────┬───────────────────────────────┬──────────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE BIGQUERY                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Raw Tables:                                              │  │
│  │  - events_*  (GA4 events, partitioned by date)           │  │
│  │  - events_streaming (real-time ingestion target)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DBT TRANSFORMATION                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  STAGING LAYER (stg_)                                     │  │
│  │  - stg_ga4_events: Flatten nested fields, clean data     │  │
│  │  - stg_ga4_sessions: Sessionize events                   │  │
│  │  - stg_ga4_conversions: Filter conversion events         │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  INTERMEDIATE LAYER (int_)                                │  │
│  │  - int_user_journeys: User touchpoint sequences          │  │
│  │  - int_touchpoints: Deduplicated touchpoints             │  │
│  │  - int_conversions: Conversions with attribution window  │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MARTS LAYER (mart_)                                      │  │
│  │  - mart_first_click_attribution                           │  │
│  │  - mart_last_click_attribution                            │  │
│  │  - mart_attribution_comparison                            │  │
│  │  - mart_channel_performance                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REAL-TIME DASHBOARD                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Streamlit Application                                    │  │
│  │  - First vs Last Attribution Metrics                      │  │
│  │  - 14-Day Time Series Chart                               │  │
│  │  - Channel Breakdown (Pie/Bar Chart)                      │  │
│  │  - Live Event Feed (Auto-refresh every 5s)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Sources

#### GA4 Public Dataset
- **Dataset**: `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
- **Table Pattern**: `events_YYYYMMDD` (date-partitioned)
- **Update Frequency**: Static (sample data)
- **Key Fields**:
  - `event_name`: Type of event (page_view, purchase, etc.)
  - `user_pseudo_id`: Anonymous user identifier
  - `event_timestamp`: Microsecond precision timestamp
  - `traffic_source`: Source, medium, campaign info (nested)
  - `ecommerce`: Transaction data (nested)

#### Streaming Events
- **Target Table**: `<your-project>.attribution_data.events_streaming`
- **Schema**: Matches GA4 events schema
- **Purpose**: Demonstrate real-time ingestion and materialization
- **Deduplication**: Using `event_id` as primary key

### 2. BigQuery Storage

#### Raw Tables
- **events_*** (GA4 public data)
  - Partitioned by: `event_date` (YYYYMMDD)
  - Clustered by: `event_name`, `user_pseudo_id`
  
- **events_streaming** (real-time ingestion)
  - Partitioned by: `_PARTITIONTIME`
  - Clustered by: `event_name`, `event_timestamp`
  - TTL: 7 days (cost optimization)

### 3. dbt Transformation Pipeline

#### Staging Models (`models/staging/`)

**stg_ga4_events.sql**
```sql
-- Purpose: Flatten nested GA4 events, standardize schema
-- Materialization: View (low cost, always fresh)
-- Key transformations:
  - Unnest event_params array
  - Extract traffic_source fields
  - Convert timestamps to TIMESTAMP type
  - Filter out invalid events
```

**stg_ga4_sessions.sql**
```sql
-- Purpose: Sessionize events based on 30-minute timeout
-- Materialization: Incremental (partitioned by event_date)
-- Logic:
  - Group events by user_pseudo_id and session_id
  - Calculate session start/end times
  - Identify traffic source at session level
```

**stg_ga4_conversions.sql**
```sql
-- Purpose: Extract and validate conversion events
-- Materialization: View
-- Conversion events: purchase, begin_checkout
```

#### Intermediate Models (`models/intermediate/`)

**int_user_journeys.sql**
```sql
-- Purpose: Build user journey with ordered touchpoints
-- Materialization: Incremental (partitioned by conversion_date)
-- Logic:
  - Window function to order touchpoints chronologically
  - Filter touchpoints within 14-day lookback window
  - Handle multi-touch scenarios
```

**int_touchpoints.sql**
```sql
-- Purpose: Deduplicate and enrich touchpoints
-- Materialization: Incremental
-- Deduplication strategy:
  - Keep first occurrence within same channel/day
  - Preserve all distinct channels in user journey
```

#### Marts Models (`models/marts/`)

**mart_first_click_attribution.sql**
```sql
-- Purpose: Attribute conversions to first touchpoint
-- Materialization: Table (for dashboard performance)
-- Logic:
  - ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY touchpoint_time ASC)
  - WHERE rn = 1
-- Outputs: conversion_value, attributed_channel, conversion_count
```

**mart_last_click_attribution.sql**
```sql
-- Purpose: Attribute conversions to last touchpoint
-- Materialization: Table
-- Logic:
  - ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY touchpoint_time DESC)
  - WHERE rn = 1
```

**mart_attribution_comparison.sql**
```sql
-- Purpose: Side-by-side comparison of attribution models
-- Materialization: Table
-- Metrics: Total conversions, revenue, channel shifts
```

### 4. Streaming Pipeline

**Technology**: Python 3.9+ with BigQuery Streaming API

**Components**:
- `stream_events.py`: Main streaming script
- `event_generator.py`: Synthetic event generation
- `idempotency.py`: Deduplication logic

**Key Features**:
1. **Event Generation**
   - Generates 5-20 realistic GA4 events
   - Randomized user journeys (page_view → add_to_cart → purchase)
   - Multiple traffic sources (google, facebook, direct, email)

2. **Deduplication Strategy**
   - Generate unique `event_id` = `SHA256(user_id + event_name + timestamp)`
   - BigQuery streaming buffer: Use `insertId` parameter
   - Application-level: Check for duplicate `event_id` before insert

3. **Idempotency**
   - Events can be replayed without creating duplicates
   - Uses BigQuery's `insertId` for automatic deduplication (1-minute window)
   - Additional table-level MERGE for longer-term deduplication

4. **Latency Tracking**
   - Track time from event generation → BigQuery insert → dbt refresh
   - Expected latency: 2-5 seconds for streaming buffer
   - dbt incremental refresh: ~10-30 seconds

**Error Handling**:
- Retry logic with exponential backoff
- Dead letter queue for failed events
- Monitoring alerts for insertion failures

### 5. Real-time Dashboard

**Technology**: Streamlit with BigQuery connector

**Features**:

1. **Attribution Metrics Panel**
   - KPI cards: First-click conversions, Last-click conversions
   - Value comparison: Revenue attributed by each model
   - Percentage difference indicator

2. **14-Day Time Series**
   - Line chart: Daily conversions over 14 days
   - Dual axis: First-click vs Last-click trends
   - Interactive date filtering

3. **Channel Breakdown**
   - Pie chart: Conversion share by channel
   - Bar chart: Side-by-side first vs last attribution
   - Channels: Google, Facebook, Direct, Email, Referral

4. **Live Event Feed**
   - Auto-refresh: Every 5 seconds
   - Shows last 20 streamed events
   - Displays: timestamp, event_name, user_id, channel
   - Status indicator: Green (fresh) / Yellow (stale)

**Performance Optimizations**:
- Query caching (5-minute TTL)
- Pre-aggregated tables in dbt
- Streamlit session state for reduced queries
- Async queries for large datasets

### 6. Monitoring & Operations

**Monitoring Points**:
1. dbt Cloud: Model run status, test failures
2. BigQuery: Query performance, slot usage
3. Streaming: Event insertion rate, error rate
4. Dashboard: Query latency, user sessions

**Alerting**:
- dbt test failures → Email/Slack
- Streaming pipeline down > 5 min → Page
- Dashboard errors → Log aggregation

**Cost Management**:
- BigQuery slot reservations for predictable cost
- Table partitioning and clustering
- Query result caching
- Streaming buffer cleanup (7-day TTL)

## Data Lineage

```
GA4 Events (Raw)
  └─> stg_ga4_events (View)
        └─> stg_ga4_sessions (Incremental)
              └─> int_user_journeys (Incremental)
                    └─> int_touchpoints (Incremental)
                          ├─> mart_first_click_attribution (Table)
                          ├─> mart_last_click_attribution (Table)
                          └─> mart_attribution_comparison (Table)
                                └─> Dashboard (Streamlit)
```

## Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Data Warehouse | Google BigQuery | Scalable, serverless, native GA4 integration |
| Transformation | dbt | SQL-based, version-controlled, testable models |
| Streaming | Python + BigQuery API | Flexible, easy to demonstrate, low latency |
| Dashboard | Streamlit | Fast development, Python-native, auto-refresh |
| Orchestration | dbt Cloud | (Optional) For production scheduling |
| Version Control | Git | Required for submission, best practice |

## Scalability Considerations

1. **BigQuery**:
   - Auto-scaling compute
   - Partitioning handles large datasets efficiently
   - Clustering improves query performance

2. **dbt**:
   - Incremental models for large fact tables
   - Snapshot support for slowly changing dimensions
   - Parallel execution of independent models

3. **Streaming**:
   - Can scale to thousands of events/second with BigQuery streaming
   - Consider Apache Beam / Dataflow for production scale
   - Pub/Sub for event buffering and retry

4. **Dashboard**:
   - Pre-aggregated tables reduce query load
   - Consider caching layer (Redis) for production
   - Materialize views for frequently accessed data

## Security & Compliance

- **Authentication**: Service account with minimal IAM permissions
- **Data Privacy**: GA4 public data is already anonymized
- **Encryption**: At-rest and in-transit (BigQuery default)
- **Audit Logs**: BigQuery audit logs enabled for compliance

## Estimated Costs (Monthly)

- BigQuery Storage: ~$2-5 (1GB active, 5GB long-term)
- BigQuery Compute: ~$3-8 (based on query volume)
- Streaming Inserts: ~$1-3 (up to 100K events)
- Dashboard Hosting: $0 (Streamlit Community Cloud)
- **Total**: ~$6-16/month

## Future Enhancements

1. **Multi-touch Attribution**: Linear, time-decay, position-based models
2. **Machine Learning**: Data-driven attribution with AutoML
3. **Cross-device Tracking**: User ID stitching
4. **A/B Testing**: Campaign attribution experiments
5. **Real-time Alerts**: Anomaly detection on conversion rates

---

**Last Updated**: Nov 12, 2025  
**Version**: 1.0
