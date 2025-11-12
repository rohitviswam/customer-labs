/*
    Staging model for GA4 conversions
    
    Purpose:
    - Extract and validate conversion events
    - Prepare for attribution analysis
    
    Dependencies: stg_ga4_events
*/

{{ config(
    materialized='view',
    tags=['staging', 'ga4', 'conversions']
) }}

with events as (
    select *
    from {{ ref('stg_ga4_events') }}
),

conversions as (
    select
        -- Conversion identification
        concat(
            user_pseudo_id,
            '-',
            event_name,
            '-',
            cast(event_timestamp as string)
        ) as conversion_id,
        
        event_id,
        parse_date('%Y%m%d', event_date) as conversion_date,
        event_datetime as conversion_datetime,
        event_timestamp as conversion_timestamp,
        event_name as conversion_event,
        
        -- User identification
        user_pseudo_id,
        user_id,
        session_id,
        
        -- Conversion value
        coalesce(purchase_revenue, event_value, 0) as conversion_value,
        transaction_id,
        total_item_quantity,
        
        -- Attribution window lookback (14 days)
        timestamp_sub(event_datetime, interval {{ var('attribution_lookback_days', 14) }} day) as attribution_window_start,
        event_datetime as attribution_window_end,
        
        -- Context
        channel as conversion_channel,
        traffic_source as conversion_traffic_source,
        page_location as conversion_page,
        
        -- Device and geo
        device_category,
        device_os,
        country,
        city,
        
        -- Conversion type hierarchy
        case
            when event_name = 'purchase' then 1
            when event_name = 'begin_checkout' then 2
            when event_name = 'add_to_cart' then 3
            else 99
        end as conversion_priority,
        
        -- Metadata
        current_timestamp() as _loaded_at
        
    from events
    where
        -- Filter to conversion events
        event_name in unnest({{ var('conversion_events', ['purchase', 'begin_checkout']) }})
        
        -- Data quality filters
        and user_pseudo_id is not null
        and event_datetime is not null
        and event_datetime >= timestamp('2020-01-01')
)

select * from conversions
