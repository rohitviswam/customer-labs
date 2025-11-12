/*
    Mart: Last-Click Attribution
    
    Purpose:
    - Attribute 100% of conversion credit to last touchpoint before conversion
    - Aggregate by channel and date
    
    Dependencies: int_user_journeys
*/

{{ config(
    materialized='view',
    tags=['marts', 'attribution']
) }}

with journeys as (
    select *
    from {{ ref('int_user_journeys') }}
),

-- Get last touchpoint for each conversion
last_touch as (
    select
        conversion_id,
        conversion_date,
        conversion_datetime,
        conversion_event,
        conversion_value,
        transaction_id,
        user_pseudo_id,
        
        -- Last touchpoint details
        channel as attributed_channel,
        traffic_source as attributed_source,
        traffic_medium as attributed_medium,
        traffic_campaign as attributed_campaign,
        landing_page as attributed_landing_page,
        touchpoint_date as attributed_touchpoint_date,
        touchpoint_datetime as attributed_touchpoint_datetime,
        
        -- Journey context
        total_touchpoints,
        journey_type,
        journey_length_days,
        days_to_conversion as last_touch_to_conversion_days,
        
        -- Conversion context
        conversion_channel,
        conversion_device,
        conversion_country,
        
        'Last-Click' as attribution_model
        
    from journeys
    where is_last_touchpoint = true
),

-- Handle direct conversions (no prior touchpoints)
direct_conversions as (
    select
        c.conversion_id,
        c.conversion_date,
        c.conversion_datetime,
        c.conversion_event,
        c.conversion_value,
        c.transaction_id,
        c.user_pseudo_id,
        
        -- Attribute to conversion channel itself
        c.conversion_channel as attributed_channel,
        c.conversion_traffic_source as attributed_source,
        'direct' as attributed_medium,
        cast(null as string) as attributed_campaign,
        c.conversion_page as attributed_landing_page,
        c.conversion_date as attributed_touchpoint_date,
        c.conversion_datetime as attributed_touchpoint_datetime,
        
        -- Journey metrics
        1 as total_touchpoints,
        'Single Touch' as journey_type,
        0 as journey_length_days,
        0 as last_touch_to_conversion_days,
        
        -- Context
        c.conversion_channel,
        c.device_category as conversion_device,
        c.country as conversion_country,
        
        'Last-Click' as attribution_model
        
    from {{ ref('stg_ga4_conversions') }} c
    left join journeys j
        on c.conversion_id = j.conversion_id
    where j.conversion_id is null  -- No touchpoints found
),

-- Union attributed and direct conversions
all_attributed as (
    select * from last_touch
    union all
    select * from direct_conversions
)

select * from all_attributed
