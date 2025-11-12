/*
    Staging model for GA4 events
    
    Purpose:
    - Flatten nested GA4 event structure
    - Extract and standardize traffic source fields
    - Convert timestamps to proper format
    - Filter out invalid events
    
    Source: bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
*/

{{ config(
    materialized='view',
    tags=['staging', 'ga4']
) }}

with source_events as (
    select *
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
    where
        -- GA4 public dataset has data from 2020-2021
        _table_suffix BETWEEN '20201101' AND '20210131'
        and event_timestamp is not null
        and user_pseudo_id is not null
),

flattened_events as (
    select
        -- Event identification
        concat(
            user_pseudo_id, 
            '-', 
            event_name, 
            '-', 
            cast(event_timestamp as string)
        ) as event_id,
        event_date,
        event_timestamp,
        timestamp_micros(event_timestamp) as event_datetime,
        event_name,
        
        -- User identification
        user_pseudo_id,
        user_id,
        
        -- Session identification
        concat(user_pseudo_id, '-', cast((select value.int_value from unnest(event_params) where key = 'ga_session_id') as string)) as session_id,
        (select value.int_value from unnest(event_params) where key = 'ga_session_id') as ga_session_id,
        (select value.int_value from unnest(event_params) where key = 'ga_session_number') as ga_session_number,
        
        -- Traffic source
        coalesce(traffic_source.source, '(direct)') as traffic_source,
        coalesce(traffic_source.medium, '(none)') as traffic_medium,
        traffic_source.name as traffic_campaign,
        
        -- Derive channel from source and medium
        case
            when lower(coalesce(traffic_source.source, '')) = '(direct)' 
                and lower(coalesce(traffic_source.medium, '')) = '(none)' 
                then 'Direct'
            when lower(coalesce(traffic_source.medium, '')) in ('cpc', 'ppc', 'paid') 
                and lower(coalesce(traffic_source.source, '')) like '%google%' 
                then 'Paid Search'
            when lower(coalesce(traffic_source.medium, '')) = 'organic' 
                and lower(coalesce(traffic_source.source, '')) like '%google%' 
                then 'Organic Search'
            when lower(coalesce(traffic_source.medium, '')) in ('cpc', 'ppc', 'paid') 
                and lower(coalesce(traffic_source.source, '')) like '%facebook%' 
                then 'Paid Social'
            when lower(coalesce(traffic_source.source, '')) like '%facebook%' 
                or lower(coalesce(traffic_source.source, '')) like '%twitter%'
                or lower(coalesce(traffic_source.source, '')) like '%instagram%'
                then 'Organic Social'
            when lower(coalesce(traffic_source.medium, '')) = 'email' 
                then 'Email'
            when lower(coalesce(traffic_source.medium, '')) = 'referral' 
                then 'Referral'
            when lower(coalesce(traffic_source.medium, '')) = 'affiliate'
                then 'Affiliate'
            else 'Other'
        end as channel,
        
        -- Device information
        device.category as device_category,
        device.operating_system as device_os,
        device.web_info.browser as device_browser,
        
        -- Geography
        geo.country as country,
        geo.region as region,
        geo.city as city,
        
        -- Ecommerce data
        ecommerce.transaction_id,
        ecommerce.purchase_revenue,
        ecommerce.total_item_quantity,
        
        -- Event parameters (commonly used ones)
        (select value.string_value from unnest(event_params) where key = 'page_location') as page_location,
        (select value.string_value from unnest(event_params) where key = 'page_title') as page_title,
        (select value.int_value from unnest(event_params) where key = 'engagement_time_msec') as engagement_time_msec,
        (select value.string_value from unnest(event_params) where key = 'session_engaged') as session_engaged,
        
        -- Event value
        (select value.int_value from unnest(event_params) where key = 'value') as event_value_param,
        coalesce(
            ecommerce.purchase_revenue,
            (select value.int_value from unnest(event_params) where key = 'value')
        ) as event_value,
        
        -- Metadata
        platform,
        stream_id,
        
        -- Record info
        current_timestamp() as _loaded_at
        
    from source_events
),

final as (
    select
        *,
        -- Add data quality flags
        case 
            when traffic_source = '(direct)' and traffic_medium = '(none)' then true
            else false
        end as is_direct_traffic,
        
        case
            when event_name in ('purchase', 'begin_checkout', 'add_to_cart') then true
            else false
        end as is_conversion_event,
        
        case
            when event_name = 'page_view' then true
            else false
        end as is_pageview,
        
        -- Session start flag
        case
            when event_name = 'session_start' or ga_session_number = 1 then true
            else false
        end as is_session_start
        
    from flattened_events
    where
        -- Basic data quality filters
        event_name is not null
        and event_datetime >= timestamp('2020-01-01')
        and event_datetime <= current_timestamp()
)

select * from final
