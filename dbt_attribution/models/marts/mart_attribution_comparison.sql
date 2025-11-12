/*
    Mart: Attribution Comparison
    
    Purpose:
    - Compare First-Click and Last-Click attribution side by side
    - Show channel shifts between models
    
    Dependencies: mart_first_click_attribution, mart_last_click_attribution
*/

{{ config(
    materialized='view',
    tags=['marts', 'attribution', 'comparison']
) }}

with first_click_agg as (
    select
        attributed_channel as channel,
        conversion_date,
        count(distinct conversion_id) as first_click_conversions,
        sum(conversion_value) as first_click_revenue,
        avg(journey_length_days) as avg_journey_days_fc,
        avg(total_touchpoints) as avg_touchpoints_fc
    from {{ ref('mart_first_click_attribution') }}
    group by channel, conversion_date
),

last_click_agg as (
    select
        attributed_channel as channel,
        conversion_date,
        count(distinct conversion_id) as last_click_conversions,
        sum(conversion_value) as last_click_revenue,
        avg(journey_length_days) as avg_journey_days_lc,
        avg(total_touchpoints) as avg_touchpoints_lc
    from {{ ref('mart_last_click_attribution') }}
    group by channel, conversion_date
),

-- Full outer join to capture channels that appear in one model but not the other
combined as (
    select
        coalesce(f.channel, l.channel) as channel,
        coalesce(f.conversion_date, l.conversion_date) as conversion_date,
        
        -- First-click metrics
        coalesce(f.first_click_conversions, 0) as first_click_conversions,
        coalesce(f.first_click_revenue, 0) as first_click_revenue,
        f.avg_journey_days_fc,
        f.avg_touchpoints_fc,
        
        -- Last-click metrics
        coalesce(l.last_click_conversions, 0) as last_click_conversions,
        coalesce(l.last_click_revenue, 0) as last_click_revenue,
        l.avg_journey_days_lc,
        l.avg_touchpoints_lc,
        
        -- Attribution difference
        coalesce(l.last_click_conversions, 0) - coalesce(f.first_click_conversions, 0) as conversion_shift,
        coalesce(l.last_click_revenue, 0) - coalesce(f.first_click_revenue, 0) as revenue_shift,
        
        -- Percentage shifts
        case
            when coalesce(f.first_click_conversions, 0) > 0
            then ((coalesce(l.last_click_conversions, 0) - coalesce(f.first_click_conversions, 0)) 
                  / f.first_click_conversions * 100)
            else null
        end as conversion_shift_percent,
        
        case
            when coalesce(f.first_click_revenue, 0) > 0
            then ((coalesce(l.last_click_revenue, 0) - coalesce(f.first_click_revenue, 0)) 
                  / f.first_click_revenue * 100)
            else null
        end as revenue_shift_percent
        
    from first_click_agg f
    full outer join last_click_agg l
        on f.channel = l.channel
        and f.conversion_date = l.conversion_date
)

select * from combined
order by conversion_date desc, channel
