"""
Real-time Attribution Dashboard

A Streamlit dashboard that displays:
1. First-Click vs Last-Click attribution metrics
2. 14-day time series comparison
3. Channel breakdown
4. Live event feed

Usage:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Attribution Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize BigQuery client
@st.cache_resource
def get_bigquery_client():
    """Initialize and cache BigQuery client"""
    return bigquery.Client()

# Data loading functions with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_attribution_summary(_client, project_id, dataset_id):
    """Load aggregated attribution metrics"""
    query = f"""
    WITH first_click AS (
        SELECT
            COUNT(DISTINCT conversion_id) as conversions,
            SUM(conversion_value) as revenue,
            COUNT(DISTINCT user_pseudo_id) as users
        FROM `{project_id}.{dataset_id}.mart_first_click_attribution`
        WHERE conversion_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    ),
    last_click AS (
        SELECT
            COUNT(DISTINCT conversion_id) as conversions,
            SUM(conversion_value) as revenue,
            COUNT(DISTINCT user_pseudo_id) as users
        FROM `{project_id}.{dataset_id}.mart_last_click_attribution`
        WHERE conversion_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    )
    SELECT
        'First-Click' as model,
        fc.conversions,
        fc.revenue,
        fc.users
    FROM first_click fc
    UNION ALL
    SELECT
        'Last-Click' as model,
        lc.conversions,
        lc.revenue,
        lc.users
    FROM last_click lc
    """
    
    return _client.query(query).to_dataframe()

@st.cache_data(ttl=300)
def load_time_series(_client, project_id, dataset_id):
    """Load 14-day time series for both attribution models"""
    query = f"""
    SELECT
        conversion_date,
        channel,
        first_click_conversions,
        last_click_conversions,
        first_click_revenue,
        last_click_revenue
    FROM `{project_id}.{dataset_id}.mart_attribution_comparison`
    WHERE conversion_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    ORDER BY conversion_date
    """
    
    return _client.query(query).to_dataframe()

@st.cache_data(ttl=300)
def load_channel_breakdown(_client, project_id, dataset_id):
    """Load channel-level attribution breakdown"""
    query = f"""
    WITH first_click AS (
        SELECT
            attributed_channel as channel,
            COUNT(DISTINCT conversion_id) as conversions,
            SUM(conversion_value) as revenue
        FROM `{project_id}.{dataset_id}.mart_first_click_attribution`
        WHERE conversion_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
        GROUP BY channel
    ),
    last_click AS (
        SELECT
            attributed_channel as channel,
            COUNT(DISTINCT conversion_id) as conversions,
            SUM(conversion_value) as revenue
        FROM `{project_id}.{dataset_id}.mart_last_click_attribution`
        WHERE conversion_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
        GROUP BY channel
    )
    SELECT
        COALESCE(f.channel, l.channel) as channel,
        COALESCE(f.conversions, 0) as first_click_conversions,
        COALESCE(l.conversions, 0) as last_click_conversions,
        COALESCE(f.revenue, 0) as first_click_revenue,
        COALESCE(l.revenue, 0) as last_click_revenue
    FROM first_click f
    FULL OUTER JOIN last_click l ON f.channel = l.channel
    ORDER BY last_click_conversions DESC
    """
    
    return _client.query(query).to_dataframe()

@st.cache_data(ttl=5)  # Cache for only 5 seconds - near real-time
def load_live_events(_client, project_id, dataset_id, limit=20):
    """Load recent streamed events"""
    query = f"""
    SELECT
        event_id,
        event_name,
        user_pseudo_id,
        TIMESTAMP_MICROS(event_timestamp) as event_time,
        traffic_source.source as source,
        traffic_source.medium as medium,
        ingestion_timestamp,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), ingestion_timestamp, SECOND) as seconds_ago
    FROM `{project_id}.{dataset_id}.events_streaming`
    ORDER BY ingestion_timestamp DESC
    LIMIT {limit}
    """
    
    try:
        return _client.query(query).to_dataframe()
    except Exception as e:
        return pd.DataFrame()  # Return empty if streaming table doesn't exist yet

# Main dashboard
def main():
    # Sidebar configuration
    st.sidebar.title("⚙️ Configuration")
    
    project_id = st.sidebar.text_input(
        "GCP Project ID",
        value="your-project-id",
        help="Enter your Google Cloud Project ID"
    )
    
    dataset_id = st.sidebar.text_input(
        "Dataset ID",
        value="attribution_dev",
        help="BigQuery dataset containing dbt models"
    )
    
    auto_refresh = st.sidebar.checkbox("Auto-refresh (every 10s)", value=False)
    
    if auto_refresh:
        st.sidebar.info("Dashboard will refresh every 10 seconds")
    
    # Header
    st.markdown('<div class="main-header">📊 Real-time Attribution Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize client
    try:
        client = get_bigquery_client()
    except Exception as e:
        st.error(f"❌ Failed to initialize BigQuery client: {str(e)}")
        st.info("Please ensure Google Cloud credentials are configured correctly.")
        return
    
    # Load data
    try:
        with st.spinner("Loading attribution data..."):
            summary_df = load_attribution_summary(client, project_id, dataset_id)
            time_series_df = load_time_series(client, project_id, dataset_id)
            channel_df = load_channel_breakdown(client, project_id, dataset_id)
            live_events_df = load_live_events(client, project_id, dataset_id)
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.info("Make sure you've run `dbt run` and the dataset/tables exist.")
        return
    
    # Section 1: Attribution Metrics Overview
    st.header("1. Attribution Model Comparison")
    
    col1, col2, col3, col4 = st.columns(4)
    
    if not summary_df.empty:
        fc_data = summary_df[summary_df['model'] == 'First-Click'].iloc[0]
        lc_data = summary_df[summary_df['model'] == 'Last-Click'].iloc[0]
        
        with col1:
            st.metric(
                "First-Click Conversions",
                f"{int(fc_data['conversions']):,}",
                delta=None
            )
        
        with col2:
            st.metric(
                "Last-Click Conversions",
                f"{int(lc_data['conversions']):,}",
                delta=f"{int(lc_data['conversions'] - fc_data['conversions']):+,}"
            )
        
        with col3:
            st.metric(
                "First-Click Revenue",
                f"${fc_data['revenue']:,.2f}",
                delta=None
            )
        
        with col4:
            st.metric(
                "Last-Click Revenue",
                f"${lc_data['revenue']:,.2f}",
                delta=f"${lc_data['revenue'] - fc_data['revenue']:+,.2f}"
            )
    else:
        st.warning("No attribution data available. Run dbt models first.")
    
    st.markdown("---")
    
    # Section 2: 14-Day Time Series
    st.header("2. 14-Day Attribution Trends")
    
    if not time_series_df.empty:
        # Aggregate by date
        daily_agg = time_series_df.groupby('conversion_date').agg({
            'first_click_conversions': 'sum',
            'last_click_conversions': 'sum',
            'first_click_revenue': 'sum',
            'last_click_revenue': 'sum'
        }).reset_index()
        
        # Conversions time series
        fig_conversions = go.Figure()
        fig_conversions.add_trace(go.Scatter(
            x=daily_agg['conversion_date'],
            y=daily_agg['first_click_conversions'],
            name='First-Click',
            line=dict(color='#636EFA', width=3),
            mode='lines+markers'
        ))
        fig_conversions.add_trace(go.Scatter(
            x=daily_agg['conversion_date'],
            y=daily_agg['last_click_conversions'],
            name='Last-Click',
            line=dict(color='#EF553B', width=3),
            mode='lines+markers'
        ))
        fig_conversions.update_layout(
            title="Daily Conversions by Attribution Model",
            xaxis_title="Date",
            yaxis_title="Conversions",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_conversions, use_container_width=True)
        
        # Revenue time series
        fig_revenue = go.Figure()
        fig_revenue.add_trace(go.Scatter(
            x=daily_agg['conversion_date'],
            y=daily_agg['first_click_revenue'],
            name='First-Click',
            line=dict(color='#636EFA', width=3),
            mode='lines+markers'
        ))
        fig_revenue.add_trace(go.Scatter(
            x=daily_agg['conversion_date'],
            y=daily_agg['last_click_revenue'],
            name='Last-Click',
            line=dict(color='#EF553B', width=3),
            mode='lines+markers'
        ))
        fig_revenue.update_layout(
            title="Daily Revenue by Attribution Model",
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    else:
        st.warning("No time series data available.")
    
    st.markdown("---")
    
    # Section 3: Channel Breakdown
    st.header("3. Channel Performance Breakdown")
    
    if not channel_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # First-Click pie chart
            fig_fc_pie = px.pie(
                channel_df,
                values='first_click_conversions',
                names='channel',
                title='First-Click Attribution by Channel',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_fc_pie, use_container_width=True)
        
        with col2:
            # Last-Click pie chart
            fig_lc_pie = px.pie(
                channel_df,
                values='last_click_conversions',
                names='channel',
                title='Last-Click Attribution by Channel',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_lc_pie, use_container_width=True)
        
        # Side-by-side comparison bar chart
        fig_comparison = go.Figure()
        fig_comparison.add_trace(go.Bar(
            name='First-Click',
            x=channel_df['channel'],
            y=channel_df['first_click_conversions'],
            marker_color='#636EFA'
        ))
        fig_comparison.add_trace(go.Bar(
            name='Last-Click',
            x=channel_df['channel'],
            y=channel_df['last_click_conversions'],
            marker_color='#EF553B'
        ))
        fig_comparison.update_layout(
            title='Conversions by Channel: First-Click vs Last-Click',
            xaxis_title='Channel',
            yaxis_title='Conversions',
            barmode='group',
            height=400
        )
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Data table
        st.subheader("Channel Metrics Table")
        display_df = channel_df.copy()
        display_df['first_click_revenue'] = display_df['first_click_revenue'].apply(lambda x: f"${x:,.2f}")
        display_df['last_click_revenue'] = display_df['last_click_revenue'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("No channel data available.")
    
    st.markdown("---")
    
    # Section 4: Live Event Feed
    st.header("4. 🔴 Live Event Feed")
    
    if not live_events_df.empty:
        # Status indicator
        most_recent_seconds = live_events_df['seconds_ago'].min()
        if most_recent_seconds < 60:
            st.success(f"✅ Live - Last event received {int(most_recent_seconds)} seconds ago")
        elif most_recent_seconds < 300:
            st.warning(f"⚠️ Recent - Last event received {int(most_recent_seconds)} seconds ago")
        else:
            st.error(f"❌ Stale - Last event received {int(most_recent_seconds)} seconds ago")
        
        # Format for display
        display_events = live_events_df[['event_time', 'event_name', 'source', 'medium', 'user_pseudo_id', 'seconds_ago']].copy()
        display_events['event_time'] = pd.to_datetime(display_events['event_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        display_events['seconds_ago'] = display_events['seconds_ago'].apply(lambda x: f"{int(x)}s ago")
        
        st.dataframe(
            display_events,
            use_container_width=True,
            height=400,
            column_config={
                "event_time": "Timestamp",
                "event_name": "Event",
                "source": "Source",
                "medium": "Medium",
                "user_pseudo_id": "User ID",
                "seconds_ago": "Age"
            }
        )
    else:
        st.info("No live events yet. Run the streaming pipeline to see real-time data.")
        st.code("python streaming/stream_events.py --project YOUR_PROJECT --dataset attribution_data")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()
