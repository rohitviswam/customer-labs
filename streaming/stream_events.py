"""
Real-time Event Streaming Pipeline

This script demonstrates near-real-time ingestion of GA4-like events into BigQuery.
It generates synthetic events and streams them with deduplication and idempotency.

Usage:
    python stream_events.py --project YOUR_PROJECT --dataset attribution_data --num-events 10
"""

import argparse
import hashlib
import json
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from google.cloud import bigquery
from google.api_core import retry


class EventStreamer:
    """Streams events to BigQuery with deduplication and latency tracking"""
    
    def __init__(self, project_id: str, dataset_id: str, table_id: str = "events_streaming"):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.full_table_id = f"{project_id}.{dataset_id}.{table_id}"
        
        # Event generation configuration
        self.channels = [
            ("google", "cpc", "spring_sale"),
            ("google", "organic", None),
            ("facebook", "cpc", "retargeting"),
            ("(direct)", "(none)", None),
            ("email", "email", "newsletter"),
        ]
        
        self.event_types = [
            "page_view",
            "session_start",
            "view_item",
            "add_to_cart",
            "begin_checkout",
            "purchase"
        ]
        
        self.products = [
            {"id": "PROD001", "name": "Widget A", "price": 29.99},
            {"id": "PROD002", "name": "Gadget B", "price": 49.99},
            {"id": "PROD003", "name": "Tool C", "price": 79.99},
        ]
        
    def ensure_table_exists(self):
        """Create the streaming table if it doesn't exist"""
        schema = [
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("event_timestamp", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("event_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_pseudo_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("event_params", "RECORD", mode="REPEATED", fields=[
                bigquery.SchemaField("key", "STRING"),
                bigquery.SchemaField("value", "RECORD", fields=[
                    bigquery.SchemaField("string_value", "STRING"),
                    bigquery.SchemaField("int_value", "INTEGER"),
                    bigquery.SchemaField("float_value", "FLOAT"),
                ])
            ]),
            bigquery.SchemaField("traffic_source", "RECORD", fields=[
                bigquery.SchemaField("source", "STRING"),
                bigquery.SchemaField("medium", "STRING"),
                bigquery.SchemaField("name", "STRING"),
            ]),
            bigquery.SchemaField("device", "RECORD", fields=[
                bigquery.SchemaField("category", "STRING"),
                bigquery.SchemaField("operating_system", "STRING"),
                bigquery.SchemaField("browser", "STRING"),
            ]),
            bigquery.SchemaField("geo", "RECORD", fields=[
                bigquery.SchemaField("country", "STRING"),
                bigquery.SchemaField("region", "STRING"),
                bigquery.SchemaField("city", "STRING"),
            ]),
            bigquery.SchemaField("ecommerce", "RECORD", fields=[
                bigquery.SchemaField("transaction_id", "STRING"),
                bigquery.SchemaField("purchase_revenue", "FLOAT"),
                bigquery.SchemaField("total_item_quantity", "INTEGER"),
            ]),
            bigquery.SchemaField("stream_id", "STRING"),
            bigquery.SchemaField("platform", "STRING"),
            bigquery.SchemaField("ingestion_timestamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        table = bigquery.Table(self.full_table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="event_date"
        )
        table.clustering_fields = ["event_name", "user_pseudo_id"]
        
        try:
            table = self.client.create_table(table)
            print(f"✓ Created table {self.full_table_id}")
        except Exception as e:
            if "Already Exists" in str(e):
                print(f"✓ Table {self.full_table_id} already exists")
            else:
                raise
    
    def generate_event_id(self, user_id: str, event_name: str, timestamp: int) -> str:
        """Generate deterministic event ID for deduplication"""
        unique_string = f"{user_id}-{event_name}-{timestamp}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def generate_user_journey(self, user_id: str, num_events: int = 5) -> List[Dict]:
        """Generate a realistic user journey"""
        events = []
        base_time = datetime.utcnow() - timedelta(minutes=random.randint(1, 60))
        
        # Pick a channel for this journey
        source, medium, campaign = random.choice(self.channels)
        
        # Session ID
        session_id = random.randint(1000000, 9999999)
        session_number = random.randint(1, 10)
        
        # Generate journey events
        journey_types = ["page_view", "view_item", "add_to_cart", "begin_checkout", "purchase"]
        for i, event_name in enumerate(journey_types[:num_events]):
            event_time = base_time + timedelta(seconds=i * random.randint(30, 300))
            event_timestamp = int(event_time.timestamp() * 1_000_000)  # Microseconds
            
            event = {
                "event_id": self.generate_event_id(user_id, event_name, event_timestamp),
                "event_date": event_time.date().isoformat(),
                "event_timestamp": event_timestamp,
                "event_name": event_name,
                "user_pseudo_id": user_id,
                "user_id": None,
                "event_params": [
                    {"key": "ga_session_id", "value": {"int_value": session_id}},
                    {"key": "ga_session_number", "value": {"int_value": session_number}},
                    {"key": "page_location", "value": {"string_value": f"https://example.com/{event_name}"}},
                    {"key": "engagement_time_msec", "value": {"int_value": random.randint(1000, 30000)}},
                ],
                "traffic_source": {
                    "source": source,
                    "medium": medium,
                    "name": campaign,
                },
                "device": {
                    "category": random.choice(["mobile", "desktop", "tablet"]),
                    "operating_system": random.choice(["iOS", "Android", "Windows", "macOS"]),
                    "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
                },
                "geo": {
                    "country": random.choice(["US", "UK", "CA", "AU"]),
                    "region": random.choice(["California", "New York", "London", "Ontario"]),
                    "city": random.choice(["San Francisco", "New York", "London", "Toronto"]),
                },
                "stream_id": "web_stream_001",
                "platform": "WEB",
                "ingestion_timestamp": datetime.utcnow().isoformat(),
            }
            
            # Add ecommerce data for purchase events
            if event_name == "purchase":
                product = random.choice(self.products)
                quantity = random.randint(1, 3)
                event["ecommerce"] = {
                    "transaction_id": str(uuid.uuid4())[:8],
                    "purchase_revenue": product["price"] * quantity,
                    "total_item_quantity": quantity,
                }
            
            events.append(event)
        
        return events
    
    @retry.Retry(deadline=30)
    def stream_events(self, events: List[Dict]) -> Dict:
        """Stream events to BigQuery with retry logic"""
        start_time = time.time()
        
        # Use insertId for BigQuery's built-in deduplication (1-minute window)
        rows_to_insert = []
        for event in events:
            row = (event, event["event_id"])  # (row_data, insert_id)
            rows_to_insert.append(row)
        
        errors = self.client.insert_rows_json(
            self.full_table_id,
            [r[0] for r in rows_to_insert],
            row_ids=[r[1] for r in rows_to_insert]
        )
        
        latency = time.time() - start_time
        
        if errors:
            print(f"✗ Errors inserting rows: {errors}")
            return {"success": False, "errors": errors, "latency_seconds": latency}
        else:
            print(f"✓ Successfully streamed {len(events)} events (latency: {latency:.2f}s)")
            return {"success": True, "rows_inserted": len(events), "latency_seconds": latency}
    
    def verify_deduplication(self, event_id: str) -> bool:
        """Verify that duplicate events are not inserted"""
        query = f"""
            SELECT COUNT(*) as count
            FROM `{self.full_table_id}`
            WHERE event_id = '{event_id}'
        """
        
        result = list(self.client.query(query).result())
        count = result[0].count
        
        return count == 1
    
    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        """Query recent streamed events"""
        query = f"""
            SELECT
                event_id,
                event_name,
                user_pseudo_id,
                timestamp_micros(event_timestamp) as event_time,
                traffic_source.source as source,
                traffic_source.medium as medium,
                ingestion_timestamp
            FROM `{self.full_table_id}`
            ORDER BY ingestion_timestamp DESC
            LIMIT {limit}
        """
        
        results = self.client.query(query).result()
        return [dict(row) for row in results]


def main():
    parser = argparse.ArgumentParser(description="Stream GA4-like events to BigQuery")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--dataset", default="attribution_data", help="BigQuery dataset")
    parser.add_argument("--table", default="events_streaming", help="BigQuery table")
    parser.add_argument("--num-users", type=int, default=3, help="Number of users to simulate")
    parser.add_argument("--events-per-user", type=int, default=5, help="Events per user journey")
    parser.add_argument("--test-dedup", action="store_true", help="Test deduplication by sending duplicates")
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Real-time Attribution Pipeline - Event Streaming Demo")
    print(f"{'='*60}\n")
    
    # Initialize streamer
    streamer = EventStreamer(args.project, args.dataset, args.table)
    
    # Ensure table exists
    print("📋 Setting up BigQuery table...")
    streamer.ensure_table_exists()
    
    # Generate and stream events
    print(f"\n📊 Generating {args.num_users} user journeys...")
    all_events = []
    
    for i in range(args.num_users):
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        events = streamer.generate_user_journey(user_id, args.events_per_user)
        all_events.extend(events)
        print(f"  → User {i+1}: {user_id} - {len(events)} events")
    
    print(f"\n🚀 Streaming {len(all_events)} events to BigQuery...")
    result = streamer.stream_events(all_events)
    
    if result["success"]:
        print(f"\n✅ Stream completed successfully!")
        print(f"   • Events inserted: {result['rows_inserted']}")
        print(f"   • Latency: {result['latency_seconds']:.2f} seconds")
        print(f"   • Avg latency per event: {result['latency_seconds']/len(all_events):.3f}s")
    
    # Test deduplication if requested
    if args.test_dedup and all_events:
        print(f"\n🔄 Testing deduplication...")
        test_event = all_events[0]
        print(f"   • Re-streaming first event: {test_event['event_id']}")
        
        streamer.stream_events([test_event])
        time.sleep(2)  # Wait for data to be queryable
        
        is_unique = streamer.verify_deduplication(test_event['event_id'])
        if is_unique:
            print(f"   ✓ Deduplication working: Only 1 copy of event exists")
        else:
            print(f"   ✗ Deduplication failed: Multiple copies found")
    
    # Show recent events
    print(f"\n📋 Recent streamed events (last 10):")
    print(f"{'='*80}")
    recent = streamer.get_recent_events(limit=10)
    for event in recent:
        print(f"   {event['event_time']} | {event['event_name']:20s} | {event['source']:15s} | {event['user_pseudo_id']}")
    
    print(f"\n{'='*60}")
    print("✅ Streaming demo completed successfully!")
    print(f"{'='*60}\n")
    
    print("Next steps:")
    print("1. Run dbt to process the streamed events: `dbt run --select +marts`")
    print("2. View the dashboard to see real-time attribution")
    print("3. Stream more events and watch the dashboard update\n")


if __name__ == "__main__":
    main()
