/*
    Intermediate model: User Journeys
    
    Purpose:
    - Join conversions with their touchpoints within attribution window
    - Build ordered user journey for attribution
    
    Dependencies: stg_ga4_conversions, int_touchpoints
*/

{{ config(
    materialized='incremental',
    unique_key='journey_id',
    partition_by={
        'field': 'conversion_date',
        'data_type': 'date'
    },
    cluster_by=['user_pseudo_id', 'channel'],
    tags=['intermediate', 'attribution']
) }}

with conversions as (
    select *
    from {{ ref('stg_ga4_conversions') }}
    
    {% if is_incremental() %}
        where conversion_date >= date_sub(current_date(), interval 30 day)
    {% endif %}
),

touchpoints as (
    select *
    from {{ ref('int_touchpoints') }}
    
    {% if is_incremental() %}
        where touchpoint_date >= date_sub(current_date(), interval 45 day)  -- Extra buffer for lookback
    {% endif %}
),

-- Join conversions with touchpoints in attribution window
journeys as (
    select
        -- Journey identification
        concat(
            c.conversion_id,
            '-',
            t.touchpoint_id
        ) as journey_id,
        
        -- Conversion info
        c.conversion_id,
        c.conversion_date,
        c.conversion_datetime,
        c.conversion_timestamp,
        c.conversion_event,
        c.conversion_value,
        c.transaction_id,
        
        -- User info
        c.user_pseudo_id,
        c.user_id,
        
        -- Touchpoint info
        t.touchpoint_id,
        t.touchpoint_date,
        t.touchpoint_datetime,
        t.touchpoint_timestamp,
        t.channel,
        t.traffic_source,
        t.traffic_medium,
        t.traffic_campaign,
        t.landing_page,
        t.is_direct_traffic,
        
        -- Journey sequencing
        row_number() over (
            partition by c.conversion_id
            order by t.touchpoint_timestamp asc
        ) as touchpoint_position,
        
        count(*) over (
            partition by c.conversion_id
        ) as total_touchpoints,
        
        -- Time to conversion
        timestamp_diff(c.conversion_datetime, t.touchpoint_datetime, day) as days_to_conversion,
        timestamp_diff(c.conversion_datetime, t.touchpoint_datetime, hour) as hours_to_conversion,
        
        -- Attribution window validation
        t.touchpoint_datetime >= c.attribution_window_start as is_in_attribution_window,
        
        -- Conversion context
        c.conversion_channel,
        c.device_category as conversion_device,
        c.country as conversion_country,
        
        current_timestamp() as _updated_at
        
    from conversions c
    inner join touchpoints t
        on c.user_pseudo_id = t.user_pseudo_id
        -- Touchpoint must occur before conversion
        and t.touchpoint_timestamp < c.conversion_timestamp
        -- Touchpoint must be within attribution window
        and t.touchpoint_datetime >= c.attribution_window_start
        and t.touchpoint_datetime <= c.attribution_window_end
),

-- Add journey-level metrics
journeys_enriched as (
    select
        *,
        
        -- First and last touchpoint flags
        case when touchpoint_position = 1 then true else false end as is_first_touchpoint,
        case when touchpoint_position = total_touchpoints then true else false end as is_last_touchpoint,
        
        -- Journey type categorization
        case
            when total_touchpoints = 1 then 'Single Touch'
            when total_touchpoints = 2 then 'Two Touch'
            when total_touchpoints <= 5 then 'Short Journey (3-5)'
            when total_touchpoints <= 10 then 'Medium Journey (6-10)'
            else 'Long Journey (10+)'
        end as journey_type,
        
        -- Path length in days
        max(days_to_conversion) over (partition by conversion_id) as journey_length_days
        
    from journeys
    where is_in_attribution_window = true
)

select * from journeys_enriched
