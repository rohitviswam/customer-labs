# Design Sketches & Notes

## Sketch 1: System Architecture (Hand-drawn)

**Date:** Nov 12, 2025  
**Purpose:** Initial architecture design

```
[Photo/Scan of hand-drawn architecture diagram should be placed here]

Components sketched:
- GA4 Data Source (cloud icon)
- BigQuery (cylinder/database icon)
- dbt transformation layers (3 boxes: staging -> intermediate -> marts)
- Streaming pipeline (arrow with events)
- Dashboard (monitor/screen icon)
- Data flow arrows connecting all components
```

**Key insights from sketch:**
- Need 3 distinct dbt layers for separation of concerns
- Streaming should write to separate table
- Dashboard queries the mart tables directly
- Incremental models needed for int_ and mart_ layers

---

## Sketch 2: User Journey & Attribution Logic

**Date:** Nov 12, 2025  
**Purpose:** Map out attribution calculation logic

```
[Photo/Scan of journey flow diagram should be placed here]

Example Journey Sketched:

User A Timeline:
Day 1: Google Search (touchpoint 1) 
    ↓
Day 3: Facebook Ad (touchpoint 2)
    ↓  
Day 5: Email Click (touchpoint 3)
    ↓
Day 7: Direct Visit → PURCHASE ($100)

First-Click: Google Search gets $100
Last-Click: Email gets $100
```

**Questions noted:**
- What if multiple touchpoints on same day?
  → Keep first occurrence only
  
- What about same-channel visits?
  → Deduplicate to channel-day level
  
- Lookback window?
  → 14 days (industry standard)

---

## Sketch 3: dbt Model Dependencies

**Date:** Nov 12, 2025  
**Purpose:** Plan model lineage

```
[Photo/Scan of dependency graph should be placed here]

Boxes and arrows showing:

stg_ga4_events ────┬──→ stg_ga4_sessions
                   │
                   └──→ stg_ga4_conversions
                             │
                             ↓
                        int_touchpoints ──┐
                                          ↓
                                   int_user_journeys ──┬──→ mart_first_click
                                                       │
                                                       └──→ mart_last_click
```

**Notes:**
- Staging = views (cheap, always fresh)
- Intermediate = incremental (performance)
- Marts = tables (fast dashboard queries)

---

## Sketch 4: Dashboard Layout

**Date:** Nov 12, 2025  
**Purpose:** Wireframe dashboard UI

```
[Photo/Scan of dashboard wireframe should be placed here]

Layout sketched (4 sections):

┌─────────────────────────────────────────┐
│  📊 ATTRIBUTION DASHBOARD               │
├─────────────────────────────────────────┤
│                                          │
│  [Metric] [Metric] [Metric] [Metric]    │
│  FC Conv  LC Conv  FC Rev   LC Rev       │
│                                          │
├─────────────────────────────────────────┤
│                                          │
│  📈 14-DAY TREND                        │
│  [Line chart: First vs Last over time]  │
│                                          │
├──────────────┬──────────────────────────┤
│              │                          │
│  🥧 FIRST    │  🥧 LAST                │
│  [Pie chart] │  [Pie chart]            │
│              │                          │
├──────────────┴──────────────────────────┤
│  🔴 LIVE EVENTS                         │
│  [Table: Recent streamed events]        │
│                                          │
└─────────────────────────────────────────┘
```

**Features:**
- Auto-refresh every 5 seconds for live feed
- Comparison metrics (First vs Last)
- Time series shows trends
- Channel breakdown in pie charts

---

## Sketch 5: Event Streaming Flow

**Date:** Nov 12, 2025  
**Purpose:** Design streaming deduplication logic

```
[Photo/Scan of streaming flow should be placed here]

Flow diagram:

Event Generated
    ↓
Generate event_id = hash(user + event + timestamp)
    ↓
Use event_id as insertId for BigQuery
    ↓
BigQuery automatic dedup (1-min window)
    ↓
Additional table-level MERGE (longer term)
    ↓
Events queryable in ~2-5 seconds
    ↓
dbt incremental refresh picks up new events
```

**Deduplication strategies:**
1. insertId parameter (BQ native, 1-min window)
2. Event ID uniqueness constraint
3. MERGE statement for historical dedup

---

## Notes & Decisions

### Technical Decisions
- **Attribution window**: 14 days (balances coverage vs performance)
- **Session timeout**: 30 minutes (GA4 default)
- **Conversion priority**: purchase > begin_checkout > add_to_cart
- **Channel granularity**: Channel level only (not campaign) for MVP

### Data Quality Assumptions
- Trust GA4 event_timestamp (client-side clock)
- Filter events outside 2020-current window
- Require user_pseudo_id and event_name (must be non-null)

### Edge Cases Identified
1. Direct conversions (no prior touchpoints)
   → Attribute to "Direct" channel
   
2. Multiple conversions from same user
   → Each conversion has own 14-day window
   
3. Touchpoints at same timestamp
   → Apply tie-breaker rules (alphabetical)

### Performance Optimizations
- Partition all large tables by date
- Cluster on user_pseudo_id and event_name
- Materialize marts as tables (not views)
- Use views only for staging layer

---

## Questions for Clarification

*These would be sent within first 24 hours:*

1. ~~Should we handle refunds/negative revenue?~~
   → Decision: Exclude from MVP, track separately
   
2. ~~Campaign-level or channel-level attribution?~~
   → Decision: Channel-level for MVP
   
3. ~~Preferred lookback window (7, 14, 30 days)?~~
   → Decision: 14 days (standard)
   
4. ~~Which conversion events are most important?~~
   → Decision: `purchase` primary, `begin_checkout` secondary
   
5. ~~Real-time latency requirement (seconds vs minutes)?~~
   → Decision: Target 10-30 seconds end-to-end

---

## Implementation Notes

### Day 1 Focus
- ✓ Architecture documentation
- ✓ dbt project structure
- ✓ Staging models with flattening logic
- ✓ Schema tests

### Day 2 Focus
- ✓ Intermediate models (touchpoints, journeys)
- ✓ Attribution mart models
- ✓ Streaming pipeline script
- ✓ Deduplication logic

### Day 3 Focus
- ✓ Dashboard implementation
- ✓ Runbook and documentation
- ✓ Testing and validation
- ⏳ Demo video recording

---

**Photos/Scans Required:**
- Place actual hand-drawn sketches/photos in `/sketches/` folder
- Reference them in this document or include in final submission

**Last Updated:** Nov 12, 2025
