# Runbook - Operations Guide

## Table of Contents
1. [Setup & Installation](#setup--installation)
2. [Running the Pipeline](#running-the-pipeline)
3. [Monitoring](#monitoring)
4. [Failure Handling](#failure-handling)
5. [Maintenance](#maintenance)
6. [Cost Management](#cost-management)

---

## Setup & Installation

### Prerequisites
- Google Cloud Platform account with BigQuery enabled
- Python 3.9 or higher
- dbt 1.6+ with dbt-bigquery adapter
- Git for version control

### Initial Setup

#### 1. GCP Configuration

```bash
# Install Google Cloud SDK (if not already installed)
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable bigquerystorage.googleapis.com
```

#### 2. Service Account Setup

```bash
# Create service account
gcloud iam service-accounts create attribution-pipeline \
    --display-name="Attribution Pipeline Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:attribution-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:attribution-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Download key
gcloud iam service-accounts keys create ~/attribution-key.json \
    --iam-account=attribution-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/attribution-key.json
```

#### 3. Install Dependencies

```bash
# Clone repository
git clone <your-repo-url>
cd customer-labs

# Install dbt
pip install dbt-bigquery

# Install streaming dependencies
cd streaming
pip install -r requirements.txt

# Install dashboard dependencies
cd ../dashboard
pip install -r requirements.txt
```

#### 4. Configure dbt

```bash
cd ../dbt_attribution

# Copy profiles template
cp profiles.yml ~/.dbt/profiles.yml

# Edit with your project details
nano ~/.dbt/profiles.yml

# Update:
# - project: YOUR_PROJECT_ID
# - dataset: attribution_dev (or your preferred dataset)
# - keyfile: /path/to/attribution-key.json

# Test connection
dbt debug
```

Expected output:
```
All checks passed!
```

---

## Running the Pipeline

### Full Pipeline Execution

#### Step 1: Run dbt Models

```bash
cd dbt_attribution

# Install dbt packages (if any)
dbt deps

# Run all models
dbt run

# Expected output:
# Completed successfully
# Done. PASS=X WARN=0 ERROR=0 SKIP=0 TOTAL=X
```

**Model execution order:**
1. Staging models (`stg_*`) - ~30 seconds
2. Intermediate models (`int_*`) - ~1-2 minutes
3. Mart models (`mart_*`) - ~2-3 minutes

#### Step 2: Run dbt Tests

```bash
# Run all tests
dbt test

# Run tests for specific models
dbt test --select stg_ga4_events
dbt test --select marts
```

#### Step 3: Stream Real-time Events

```bash
cd ../streaming

# Stream 3 user journeys with 5 events each
python stream_events.py \
    --project YOUR_PROJECT_ID \
    --dataset attribution_data \
    --num-users 3 \
    --events-per-user 5

# Test deduplication
python stream_events.py \
    --project YOUR_PROJECT_ID \
    --dataset attribution_data \
    --num-users 2 \
    --test-dedup
```

#### Step 4: Launch Dashboard

```bash
cd ../dashboard

# Start Streamlit
streamlit run app.py

# Dashboard will open at http://localhost:8501
```

### Incremental Updates

For incremental updates after initial run:

```bash
# Run only models with new data
dbt run --select stg_ga4_sessions+ --full-refresh

# Run incremental models
dbt run --select int_touchpoints+ int_user_journeys+

# Run marts
dbt run --select marts
```

---

## Monitoring

### 1. dbt Monitoring

#### Check Model Run Status

```bash
# View last run summary
dbt run --select marts --log-format json | tail -20

# Check run artifacts
cat target/run_results.json | jq '.results[] | {name: .unique_id, status: .status, execution_time: .execution_time}'
```

#### Model Freshness

```bash
# Check data freshness
dbt source freshness

# Expected output should show all sources as "pass"
```

### 2. BigQuery Monitoring

#### Query Performance

```sql
-- Check job history
SELECT
    creation_time,
    job_id,
    user_email,
    statement_type,
    total_bytes_processed,
    total_slot_ms,
    ROUND(total_slot_ms / 1000, 2) as total_seconds,
    error_result.message as error
FROM `YOUR_PROJECT_ID.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
    AND statement_type = 'SELECT'
ORDER BY creation_time DESC
LIMIT 20;
```

#### Table Statistics

```sql
-- Check table sizes
SELECT
    table_name,
    ROUND(size_bytes / POW(10, 9), 2) as size_gb,
    row_count,
    creation_time
FROM `YOUR_PROJECT_ID.attribution_dev.INFORMATION_SCHEMA.TABLES`
WHERE table_type = 'BASE TABLE'
ORDER BY size_bytes DESC;
```

### 3. Streaming Pipeline Monitoring

#### Check Recent Events

```sql
SELECT
    COUNT(*) as total_events,
    COUNT(DISTINCT user_pseudo_id) as unique_users,
    MAX(ingestion_timestamp) as last_event_time,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingestion_timestamp), SECOND) as seconds_since_last
FROM `YOUR_PROJECT_ID.attribution_data.events_streaming`
WHERE ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);
```

#### Verify Deduplication

```sql
-- Check for duplicate event_ids
SELECT
    event_id,
    COUNT(*) as count
FROM `YOUR_PROJECT_ID.attribution_data.events_streaming`
GROUP BY event_id
HAVING COUNT(*) > 1;

-- Expected: 0 rows (no duplicates)
```

### 4. Dashboard Monitoring

Dashboard logs are in Streamlit's terminal output. Monitor for:
- Query execution times
- Error messages
- Data freshness warnings

### 5. Automated Alerts (Recommended)

Set up alerts using Cloud Monitoring:

```bash
# Create alert for dbt test failures
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="dbt Test Failures" \
    --condition-display-name="Test failure rate > 0" \
    --condition-threshold-value=0 \
    --condition-threshold-duration=60s
```

---

## Failure Handling

### Common Issues & Solutions

#### 1. dbt Connection Errors

**Error:** `Could not connect to BigQuery`

**Solutions:**
```bash
# Check credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS  # Should be valid JSON

# Re-authenticate
gcloud auth application-default login

# Test connection
dbt debug
```

#### 2. dbt Model Failures

**Error:** `Compilation Error` or `Runtime Error`

**Solutions:**
```bash
# Check logs
cat logs/dbt.log

# Run with verbose output
dbt run --debug

# Run specific failing model
dbt run --select <model_name> --full-refresh
```

**Common causes:**
- Schema mismatch: Run `dbt run --full-refresh`
- Partition filter issue: Check date ranges in model
- Missing dependencies: Run `dbt deps`

#### 3. BigQuery Quota Exceeded

**Error:** `Quota exceeded: Your table exceeded quota for imports`

**Solutions:**
```bash
# Check quota usage
gcloud alpha billing quotas list --service=bigquery.googleapis.com

# Request quota increase (if needed)
# https://console.cloud.google.com/iam-admin/quotas

# Reduce streaming rate temporarily
# Adjust --num-users and --events-per-user in stream_events.py
```

#### 4. Streaming Pipeline Errors

**Error:** `Failed to insert rows`

**Solutions:**
```python
# Check table schema
from google.cloud import bigquery
client = bigquery.Client()
table = client.get_table("YOUR_PROJECT.attribution_data.events_streaming")
print(table.schema)

# Verify table exists
python stream_events.py --project YOUR_PROJECT --dataset attribution_data

# Check for schema mismatches in event data
```

#### 5. Dashboard Connection Errors

**Error:** `Unable to connect to BigQuery`

**Solutions:**
1. Check credentials in Streamlit app
2. Verify dataset and project IDs in sidebar
3. Ensure tables exist: `dbt run`
4. Check firewall/network settings

### Disaster Recovery

#### Backup Strategy

```bash
# Export tables (daily cron job recommended)
bq extract \
    --destination_format=PARQUET \
    YOUR_PROJECT:attribution_dev.mart_first_click_attribution \
    gs://your-backup-bucket/backups/$(date +%Y%m%d)/first_click_*.parquet

bq extract \
    --destination_format=PARQUET \
    YOUR_PROJECT:attribution_dev.mart_last_click_attribution \
    gs://your-backup-bucket/backups/$(date +%Y%m%d)/last_click_*.parquet
```

#### Restore from Backup

```bash
# Load from backup
bq load \
    --source_format=PARQUET \
    YOUR_PROJECT:attribution_dev.mart_first_click_attribution \
    gs://your-backup-bucket/backups/20231201/first_click_*.parquet
```

#### Rebuild from Scratch

```bash
# Drop and recreate dataset
bq rm -r -f YOUR_PROJECT:attribution_dev
bq mk --dataset YOUR_PROJECT:attribution_dev

# Rerun dbt
cd dbt_attribution
dbt run --full-refresh
dbt test
```

---

## Maintenance

### Daily Tasks
- [ ] Check dashboard for data freshness
- [ ] Review error logs in BigQuery console
- [ ] Verify streaming pipeline is running

### Weekly Tasks
- [ ] Run `dbt test` and review failures
- [ ] Check BigQuery storage costs
- [ ] Review query performance metrics
- [ ] Clean up old streaming data (7+ days)

### Monthly Tasks
- [ ] Review and optimize slow queries
- [ ] Update dbt packages: `dbt deps --upgrade`
- [ ] Review and adjust attribution lookback window if needed
- [ ] Audit IAM permissions

### Quarterly Tasks
- [ ] Review and update channel mapping logic
- [ ] Analyze attribution model performance
- [ ] Consider adding new attribution models
- [ ] Review cost optimization opportunities

### Data Cleanup

```sql
-- Delete old streaming data (older than 7 days)
DELETE FROM `YOUR_PROJECT.attribution_data.events_streaming`
WHERE DATE(ingestion_timestamp) < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);

-- Vacuum deleted rows (automatic in BigQuery, but can force)
-- ALTER TABLE drops deleted rows automatically after 7 days
```

---

## Cost Management

### Current Cost Estimates

| Component | Monthly Cost (USD) |
|-----------|-------------------|
| BigQuery Storage (10 GB) | $2 |
| BigQuery Compute (100 GB processed/day) | $5 |
| Streaming Inserts (100K events/month) | $2 |
| Dashboard (Streamlit Community Cloud) | $0 |
| **Total** | **~$9/month** |

### Cost Optimization Strategies

#### 1. Partition and Cluster Tables

Already implemented in dbt models:
```sql
{{ config(
    partition_by={
        'field': 'conversion_date',
        'data_type': 'date'
    },
    cluster_by=['channel', 'user_pseudo_id']
) }}
```

#### 2. Use Views for Low-Traffic Models

Staging models use views (not tables) to reduce storage costs.

#### 3. Set Query Byte Limits

```bash
# Set user-level quota
bq mk --transfer_config \
    --target_dataset=attribution_dev \
    --display_name="Daily Limit" \
    --params='{"query":"SELECT 1","write_disposition":"WRITE_TRUNCATE"}' \
    --schedule='every day 00:00' \
    --data_source=scheduled_query
```

#### 4. Enable Long-term Storage

```bash
# Data older than 90 days automatically gets 50% discount
# No action needed - automatic in BigQuery
```

#### 5. Monitor Costs

```bash
# Check costs by service
gcloud billing accounts list
gcloud billing accounts get-iam-policy YOUR_BILLING_ACCOUNT

# Set budget alerts
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT \
    --display-name="Attribution Pipeline Budget" \
    --budget-amount=50USD \
    --threshold-rule=percent=80 \
    --threshold-rule=percent=100
```

### Cost Alerts

Set up budget alerts in GCP Console:
1. Go to Billing > Budgets & alerts
2. Create budget: $50/month
3. Set thresholds: 50%, 80%, 100%
4. Configure email notifications

---

## Performance Tuning

### Slow Query Optimization

If queries take > 10 seconds:

1. **Check table partitioning:**
   ```sql
   -- Ensure partition filter is used
   WHERE conversion_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
   ```

2. **Add clustering:**
   ```sql
   -- Already configured in dbt_project.yml
   cluster_by: ['channel', 'user_pseudo_id']
   ```

3. **Materialize intermediate results:**
   ```sql
   -- Change from view to table if needed
   {{ config(materialized='table') }}
   ```

4. **Use approximate aggregations:**
   ```sql
   -- For large datasets, use APPROX_COUNT_DISTINCT
   SELECT APPROX_COUNT_DISTINCT(user_pseudo_id) as users
   ```

---

## Support & Troubleshooting

### Debug Checklist

- [ ] Check BigQuery permissions
- [ ] Verify credentials are valid
- [ ] Ensure tables exist (`dbt ls`)
- [ ] Check dbt logs: `cat logs/dbt.log`
- [ ] Review BigQuery job history
- [ ] Verify data freshness
- [ ] Check streaming pipeline logs
- [ ] Monitor dashboard query times

### Getting Help

1. **Check logs first:**
   - dbt: `logs/dbt.log`
   - BigQuery: Console > Job History
   - Streaming: Terminal output

2. **Common commands:**
   ```bash
   dbt debug          # Test connection
   dbt run --debug    # Verbose output
   dbt test --store-failures  # Store test failures
   ```

3. **Contact:**
   - Internal: [Your Team Slack/Email]
   - dbt Community: https://community.getdbt.com
   - BigQuery Support: https://cloud.google.com/support

---

**Last Updated:** November 12, 2025  
**Version:** 1.0  
**Maintained by:** [Your Name]
