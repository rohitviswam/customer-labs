#!/usr/bin/env python3
"""Quick script to check if mart models have data"""

from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/rohitviswam/.gcp/service-account-key.json'

client = bigquery.Client(project='customer-labs-478003')

print("Checking data in models...\n")

queries = {
    "stg_ga4_events": "SELECT COUNT(*) as count FROM `customer-labs-478003.attribution_dev_staging.stg_ga4_events`",
    "stg_ga4_conversions": "SELECT COUNT(*) as count FROM `customer-labs-478003.attribution_dev_staging.stg_ga4_conversions`",
    "int_touchpoints": "SELECT COUNT(*) as count FROM `customer-labs-478003.attribution_dev_intermediate.int_touchpoints`",
    "int_user_journeys": "SELECT COUNT(*) as count FROM `customer-labs-478003.attribution_dev_intermediate.int_user_journeys`",
    "mart_first_click": "SELECT COUNT(*) as count FROM `customer-labs-478003.attribution_dev_marts.mart_first_click_attribution`",
    "mart_last_click": "SELECT COUNT(*) as count FROM `customer-labs-478003.attribution_dev_marts.mart_last_click_attribution`",
}

for name, query in queries.items():
    try:
        result = client.query(query).result()
        count = list(result)[0]['count']
        print(f"✓ {name}: {count:,} rows")
    except Exception as e:
        print(f"✗ {name}: ERROR - {str(e)[:100]}")

print("\n" + "="*50)
print("Checking sample data from mart_first_click_attribution:")
print("="*50)

sample_query = """
SELECT 
    conversion_date,
    attributed_channel,
    COUNT(*) as conversions,
    SUM(conversion_value) as revenue
FROM `customer-labs-478003.attribution_dev_marts.mart_first_click_attribution`
GROUP BY conversion_date, attributed_channel
ORDER BY conversion_date DESC
LIMIT 10
"""

try:
    result = client.query(sample_query).result()
    rows = list(result)
    if rows:
        print("\nSample data found:")
        for row in rows:
            print(f"  {row['conversion_date']} | {row['attributed_channel']:20s} | Conversions: {row['conversions']:4d} | Revenue: ${row['revenue']:,.2f}")
    else:
        print("No rows returned!")
except Exception as e:
    print(f"Error: {e}")
