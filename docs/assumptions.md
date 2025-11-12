# Assumptions & Edge Cases

## Attribution Assumptions

### 1. Lookback Window
**Assumption**: 14-day attribution window  
**Rationale**: 
- Industry standard for e-commerce attribution
- Balances between giving credit to early touchpoints and maintaining relevance
- GA4 default conversion window is 30 days, but 14 days is more conservative

**Edge Cases**:
- User journeys spanning > 14 days: Only touchpoints within 14 days before conversion are credited
- Multiple conversions from same user: Each conversion has its own 14-day lookback window

### 2. Identity Resolution

**Primary Strategy**: `user_pseudo_id` (GA4 anonymous identifier)

**Assumptions**:
- Single-device tracking (no cross-device identity resolution)
- No user login/logout handling in MVP
- Cookie-based identification is stable for 14-day window

**Edge Cases**:
1. **Missing `user_pseudo_id`**: 
   - Fallback to `ga_session_id` for session-level attribution only
   - Log warning and exclude from user-level journey analysis
   
2. **Multiple `user_pseudo_id` for same user** (e.g., different browsers):
   - Treated as separate users in MVP
   - Future enhancement: User ID stitching if `user_id` is available

3. **Cookie deletion mid-journey**:
   - Will appear as two separate user journeys
   - No attempt to merge in MVP

### 3. Session Definition

**Assumption**: 30-minute timeout (GA4 default)

**Logic**:
- New session starts if > 30 minutes between events
- Session boundary: Midnight UTC (GA4 default)

**Edge Cases**:
- Events occurring exactly at session boundary: Assigned to earlier session
- Overnight sessions (spanning midnight): Split into two sessions

### 4. Conversion Events

**Primary Conversion**: `purchase` event

**Secondary Conversions** (configurable):
- `begin_checkout`
- `add_to_cart` (micro-conversion)

**Assumptions**:
- Only one conversion credited per transaction
- If multiple conversion events occur in single session, use the highest-value event
- Hierarchy: `purchase` > `begin_checkout` > `add_to_cart`

**Edge Cases**:
1. **Multiple purchases in single session**:
   - Each purchase gets separate attribution
   - Revenue is summed for the channel

2. **Purchase without prior touchpoints** (direct conversion):
   - Attributed to "direct" channel
   - First-click = Last-click = Direct

3. **Touchpoints after conversion**:
   - Ignored for that specific conversion
   - Can be included in future conversion attribution

### 5. Channel Attribution

**Channel Mapping** (derived from `traffic_source.source` and `traffic_source.medium`):

```
google / cpc        → Paid Search
google / organic    → Organic Search
facebook / cpc      → Paid Social
facebook / organic  → Organic Social
(direct) / (none)   → Direct
email / email       → Email Marketing
```

**Assumptions**:
- UTM parameters are correctly implemented
- Referral traffic without UTMs is labeled as "Referral"
- Missing traffic source defaults to "Direct"

**Edge Cases**:
1. **Conflicting traffic source data**:
   - Trust `traffic_source` over `page_referrer`
   - If both missing, mark as "Unknown" (not "Direct")

2. **Same channel, multiple campaigns**:
   - Attribution is at channel level, not campaign level (MVP)
   - Campaign-level attribution is a future enhancement

### 6. Attribution Tie-Breakers

**Scenario**: Multiple touchpoints at exact same timestamp

**First-Click Tie-breaker**:
1. Earliest `event_timestamp`
2. If tied, alphabetically first `traffic_source.source`
3. If still tied, lowest `event_bundle_sequence_id`

**Last-Click Tie-breaker**:
1. Latest `event_timestamp`
2. If tied, alphabetically last `traffic_source.source`
3. If still tied, highest `event_bundle_sequence_id`

### 7. Revenue Attribution

**Assumption**: Full credit to single channel (100% attribution)

**Logic**:
- First-click: 100% of conversion value to first touchpoint
- Last-click: 100% of conversion value to last touchpoint

**Edge Cases**:
1. **Missing revenue data** (`ecommerce.purchase_revenue` is NULL):
   - Count as conversion but with $0 revenue
   - Include in conversion count metrics but exclude from revenue totals

2. **Negative revenue** (returns/refunds):
   - Exclude from attribution models (separate refund analysis)
   - Future: Track negative attribution for refund touchpoints

3. **Currency conversion**:
   - Assume all values are in USD (GA4 dataset is normalized)
   - No currency conversion in MVP

## Data Quality Assumptions

### 1. GA4 Event Timestamps

**Assumption**: `event_timestamp` is reliable and in microseconds since epoch

**Validation**:
- Filter out events with `event_timestamp` < 2020-01-01
- Filter out events with `event_timestamp` > NOW() + 1 day (future events)

**Edge Cases**:
- Client-side clock skew: Accept events up to 24 hours in the past
- Duplicate events: Deduplicate using `event_id` generated from `user_pseudo_id + event_name + event_timestamp`

### 2. Missing or Null Fields

| Field | Assumption | Handling |
|-------|-----------|----------|
| `user_pseudo_id` | Required | Exclude event from user-level analysis |
| `event_name` | Required | Exclude event entirely |
| `event_timestamp` | Required | Exclude event entirely |
| `traffic_source.source` | Optional | Default to "Direct" |
| `traffic_source.medium` | Optional | Default to "(none)" |
| `ecommerce.purchase_revenue` | Optional | Default to 0 |

### 3. Nested and Repeated Fields

**Assumption**: GA4 `event_params` is an array of key-value pairs

**Handling**:
- Unnest `event_params` in staging layer
- Extract relevant parameters: `page_location`, `page_title`, `value`, `currency`
- Pivot selected parameters into columns for easier querying

## Performance Assumptions

### 1. Data Volume

**Assumption**: ~1M events per day (based on GA4 sample dataset)

**Implications**:
- Incremental models required for `int_` and `mart_` layers
- Partitioning by date for all large tables
- Clustering on `user_pseudo_id` and `event_name`

### 2. Query Performance

**Assumption**: Dashboard queries should complete in < 3 seconds

**Optimizations**:
- Pre-aggregate attribution results in `mart_` tables
- Materialize tables (not views) for frequently queried data
- Use BigQuery BI Engine caching for dashboard queries

### 3. Streaming Latency

**Assumption**: Near-real-time = 5-10 seconds end-to-end latency

**Components**:
- Event generation → BigQuery insert: < 2 seconds
- BigQuery streaming buffer → queryable: < 3 seconds (streaming buffer)
- dbt incremental refresh: 10-30 seconds (manual trigger or scheduled)

## Known Limitations (MVP)

1. **No Multi-Touch Attribution**: Only first-click and last-click models
   - Future: Linear, time-decay, position-based, data-driven models

2. **No Cross-Device Tracking**: Separate devices = separate users
   - Future: User ID stitching when GA4 `user_id` is available

3. **No Campaign-Level Attribution**: Attribution at channel level only
   - Future: Campaign and creative-level granularity

4. **No Attribution Model Comparison**: First vs Last shown side-by-side, but no "channel shift" analysis
   - Future: Show which channels gain/lose credit between models

5. **No Real-time dbt**: dbt runs on schedule or manual trigger, not on every event
   - Future: Consider streaming SQL engine (Apache Flink, ksqlDB)

6. **No Historical Restatement**: If late-arriving data changes attribution, no automatic reprocessing
   - Future: Implement lookback/reprocessing windows

7. **No A/B Testing Framework**: No randomized control groups or incrementality testing
   - Future: Causal inference models for true attribution

## Testing Assumptions

### 1. Data Quality Tests (dbt)

**Assumptions about what constitutes "valid" data**:

- `user_pseudo_id` is unique per user per session
- `event_timestamp` is always increasing within a user session
- Conversion events have valid `ecommerce` data
- No duplicate `event_id` in staging tables

**Tests Implemented**:
```yaml
- unique
- not_null
- relationships (foreign key constraints)
- accepted_values (for event_name, traffic_source)
- custom tests (revenue > 0 for purchases, session_length < 24 hours)
```

### 2. Streaming Idempotency Tests

**Assumption**: Same event sent twice should only appear once

**Test Method**:
1. Generate 10 events with known `event_id`
2. Stream to BigQuery
3. Re-stream same 10 events
4. Query count should be exactly 10 (not 20)

### 3. Attribution Logic Tests

**Assumption**: Attribution calculations are deterministic and reproducible

**Test Cases**:
1. Single touchpoint journey → First = Last = Same channel
2. Two touchpoint journey → First ≠ Last
3. Multiple conversions → Each conversion attributed independently
4. No conversions → No attribution records

## Edge Case Handling Summary

| Edge Case | Handling | Impact |
|-----------|----------|--------|
| Journey > 14 days | Trim to 14 days | Older touchpoints excluded |
| Missing user_id | Use user_pseudo_id | No cross-device tracking |
| Multiple same-timestamp events | Apply tie-breaker rules | Deterministic attribution |
| Direct conversions (0 touchpoints) | Attribute to "Direct" | Ensures all conversions attributed |
| Missing revenue | Count conversion, $0 value | Conversion metrics accurate |
| Late-arriving data | Not reprocessed (MVP) | Slight undercounting possible |
| Streaming duplicates | Dedup via insertId + table merge | No duplicate events |
| Session timeout edge cases | Use GA4 30-min rule | Matches GA4 behavior |

## Questions & Clarifications Needed

*Use this section if you have clarifying questions for the hiring team (up to 5 in first 24 hours):*

1. ~~What is the preferred lookback window? (Using 14 days)~~
2. ~~Should we handle refunds/returns in attribution? (Excluding in MVP)~~
3. ~~Campaign-level vs channel-level attribution? (Channel-level in MVP)~~
4. ~~Real-time requirement: Seconds or minutes? (Targeting 10-30 seconds)~~
5. ~~Which conversion events are most important? (Using `purchase` as primary)~~

---

**Last Updated**: Nov 12, 2025  
**Version**: 1.0
