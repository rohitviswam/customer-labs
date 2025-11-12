/*
    Staging model for GA4 sessions
    
    Purpose:
    - Aggregate events into sessions
    - Calculate session-level metrics
    - Determine session traffic source (first touch)
    
    Dependencies: stg_ga4_events
*/

{{ config(
    materialized='incremental',
    unique_key='session_id',
    partition_by={
        'field': 'session_date',
        'data_type': 'date'
    },
    cluster_by=['user_pseudo_id', 'channel'],
    tags=['staging', 'ga4']
) }}

with events as (
    select *
    from {{ ref('stg_ga4_events') }}
    
    {% if is_incremental() %}
        -- Only process recent data on incremental runs
        where event_date >= date_sub(current_date(), interval 3 day)
    {% endif %}
),

session_aggregated as (
    select
        -- Session identification
        session_id,
        user_pseudo_id,
        user_id,
        
        -- Session timing
        date(min(event_datetime)) as session_date,
        min(event_datetime) as session_start_time,
        max(event_datetime) as session_end_time,
        timestamp_diff(max(event_datetime), min(event_datetime), second) as session_duration_seconds,
        
        -- Session traffic source (first touchpoint)
        array_agg(traffic_source order by event_timestamp limit 1)[offset(0)] as session_traffic_source,
        array_agg(traffic_medium order by event_timestamp limit 1)[offset(0)] as session_traffic_medium,
        array_agg(traffic_campaign order by event_timestamp limit 1)[offset(0)] as session_traffic_campaign,
        array_agg(channel order by event_timestamp limit 1)[offset(0)] as session_channel,
        
        -- Device info (first event)
        array_agg(device_category order by event_timestamp limit 1)[offset(0)] as device_category,
        array_agg(device_os order by event_timestamp limit 1)[offset(0)] as device_os,
        array_agg(device_browser order by event_timestamp limit 1)[offset(0)] as device_browser,
        
        -- Geography (first event)
        array_agg(country order by event_timestamp limit 1)[offset(0)] as country,
        array_agg(region order by event_timestamp limit 1)[offset(0)] as region,
        array_agg(city order by event_timestamp limit 1)[offset(0)] as city,
        
        -- Session metrics
        count(*) as total_events,
        countif(is_pageview) as pageviews,
        countif(is_conversion_event) as conversion_events,
        countif(event_name = 'purchase') as purchases,
        
        -- Engagement metrics
        sum(engagement_time_msec) / 1000 as engagement_time_seconds,
        max(case when session_engaged = '1' then true else false end) as is_engaged_session,
        
        -- Revenue
        sum(case when event_name = 'purchase' then coalesce(purchase_revenue, 0) else 0 end) as session_revenue,
        
        -- Landing page
        array_agg(page_location order by event_timestamp limit 1)[offset(0)] as landing_page,
        
        -- Session number
        max(ga_session_number) as ga_session_number,
        
        -- Flags
        max(is_direct_traffic) as is_direct_traffic,
        max(case when event_name = 'purchase' then true else false end) as has_purchase,
        max(case when event_name = 'begin_checkout' then true else false end) as has_checkout,
        max(case when event_name = 'add_to_cart' then true else false end) as has_add_to_cart,
        
        -- Metadata
        current_timestamp() as _updated_at
        
    from events
    group by
        session_id,
        user_pseudo_id,
        user_id
)

select * from session_aggregated
