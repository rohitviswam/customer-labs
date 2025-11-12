# Setup Instructions

Quick guide to get started with the Attribution Pipeline project.

## Prerequisites

- Python 3.9+
- Google Cloud Platform account
- Git

## Step-by-Step Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd customer-labs
```

### 2. Set Up Google Cloud

```bash
# Install gcloud CLI (if needed)
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable BigQuery
gcloud services enable bigquery.googleapis.com
```

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install dbt-bigquery pandas google-cloud-bigquery streamlit plotly
```

### 4. Configure dbt

```bash
cd dbt_attribution

# Edit profiles.yml with your project details
nano profiles.yml

# Update these fields:
# - project: YOUR_PROJECT_ID
# - dataset: attribution_dev
# - keyfile: path/to/your/credentials.json

# Copy to dbt profiles directory
mkdir -p ~/.dbt
cp profiles.yml ~/.dbt/profiles.yml

# Test connection
dbt debug
```

### 5. Run the Pipeline

```bash
# Run dbt models (this will take a few minutes)
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### 6. Stream Sample Events

```bash
cd ../streaming

# Stream 3 user journeys
python stream_events.py \
    --project YOUR_PROJECT_ID \
    --dataset attribution_dev \
    --num-users 3 \
    --events-per-user 5
```

### 7. Launch Dashboard

```bash
cd ../dashboard

# Start Streamlit
streamlit run app.py

# Open browser to http://localhost:8501
# Update project and dataset IDs in sidebar
```

## Troubleshooting

### Can't connect to BigQuery?
- Check credentials: `echo $GOOGLE_APPLICATION_CREDENTIALS`
- Re-run: `gcloud auth application-default login`
- Verify project: `gcloud config get-value project`

### dbt models failing?
- Check logs: `cat dbt_attribution/logs/dbt.log`
- Try: `dbt run --full-refresh`
- Ensure you have permissions in BigQuery

### Dashboard not loading data?
- Verify tables exist: `dbt ls`
- Check project/dataset IDs in dashboard sidebar
- Ensure models have run successfully

## Next Steps

1. Review architecture diagram in `docs/architecture.md`
2. Read operational guide in `docs/runbook.md`
3. Understand assumptions in `docs/assumptions.md`
4. Explore dbt models in `dbt_attribution/models/`

## Quick Commands Reference

```bash
# dbt
dbt run                          # Run all models
dbt test                         # Run all tests
dbt run --select marts          # Run only mart models
dbt docs generate && dbt docs serve  # Generate and view docs

# Streaming
python streaming/stream_events.py --project YOUR_PROJECT --dataset attribution_dev

# Dashboard
streamlit run dashboard/app.py

# Git
git add .
git commit -m "Your message"
git push origin main
```

## Support

For questions or issues:
- Review `docs/runbook.md` for detailed troubleshooting
- Check dbt logs in `dbt_attribution/logs/`
- Review BigQuery job history in GCP Console

Good luck! 🚀
