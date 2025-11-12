/*
    Intermediate model: User Touchpoints
    
    Purpose:
    - Deduplicate touchpoints (same channel on same day = 1 touchpoint)
    - Prepare for attribution analysis
    
    Dependencies: stg_ga4_events
*/

{{ config(
    materialized='incremental',
    unique_key='touchpoint_id',
    partition_by={
        'field': 'touchpoint_date',
        'data_type': 'date'
    },
    cluster_by=['user_pseudo_id', 'channel'],
    tags=['intermediate', 'attribution']
) }}

with events as (
    select *
    from {{ ref('stg_ga4_events') }}
    
    {% if is_incremental() %}
        where event_date >= date_sub(current_date(), interval 30 day)
    {% endif %}
),

-- Deduplicate touchpoints: Keep first occurrence per user-channel-date
deduplicated_touchpoints as (
    select
        concat(
            user_pseudo_id,
            '-',
            channel,
            '-',
            cast(event_date as string)
        ) as touchpoint_id,
        
        user_pseudo_id,
        user_id,
        session_id,
        
        event_date as touchpoint_date,
        min(event_datetime) as touchpoint_datetime,
        min(event_timestamp) as touchpoint_timestamp,
        
        channel,
        traffic_source,
        traffic_medium,
        traffic_campaign,
        
        -- Keep first page seen in this channel on this day
        array_agg(page_location order by event_timestamp limit 1)[offset(0)] as landing_page,
        
        -- Aggregate metrics for this touchpoint
        count(*) as touchpoint_event_count,
        countif(is_pageview) as touchpoint_pageviews,
        sum(engagement_time_msec) / 1000 as touchpoint_engagement_seconds,
        
        -- Device and geo from first event
        array_agg(device_category order by event_timestamp limit 1)[offset(0)] as device_category,
        array_agg(country order by event_timestamp limit 1)[offset(0)] as country,
        
        -- Flags
        max(is_direct_traffic) as is_direct_traffic,
        
        current_timestamp() as _updated_at
        
    from events
    where
        -- Exclude internal traffic if needed
        -- and geo.country != 'Internal'
        
        -- Must have valid identifiers
        user_pseudo_id is not null
        and channel is not null
        
    group by
        user_pseudo_id,
        user_id,
        session_id,
        event_date,
        channel,
        traffic_source,
        traffic_medium,
        traffic_campaign
)

select * from deduplicated_touchpoints
