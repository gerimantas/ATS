import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time
import plotly.express as px
import plotly.graph_objects as go

DB_URL = "sqlite:///ats.db"
engine = create_engine(DB_URL)

st.set_page_config(layout="wide")

@st.cache_data(ttl=10) # Cache data for 10 seconds
def load_data():
    try:
        query = "SELECT * FROM signals ORDER BY timestamp DESC LIMIT 1000"
        df = pd.read_sql(query, engine)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return pd.DataFrame()

st.title("📈 ATS Signal Monitoring Dashboard")

df = load_data()

if not df.empty:
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Signals Logged", len(df))
    avg_spread = df['spread'].mean()
    col2.metric("Average Spread", f"{avg_spread:.4f}%")
    avg_latency = df['data_latency_ms'].mean()
    col3.metric("Average Latency (ms)", f"{avg_latency:.2f}")

    # New metrics for reward analysis
    signals_with_reward = df['actual_reward'].notna()
    if signals_with_reward.any():
        avg_reward = df.loc[signals_with_reward, 'actual_reward'].mean()
        col4.metric("Average Reward", f"{avg_reward:.4f}")
        profitable_signals = (df.loc[signals_with_reward, 'actual_reward'] > 0).sum()
        win_rate = profitable_signals / signals_with_reward.sum() * 100
        col5.metric("Win Rate", f"{win_rate:.1f}%")
    else:
        col4.metric("Average Reward", "N/A")
        col5.metric("Win Rate", "N/A")

    st.subheader("Latest Generated Signals")
    st.dataframe(df)

    # New section: Reward Distribution Analysis
    st.subheader("Reward Distribution Analysis")
    if signals_with_reward.any():
        reward_df = df[signals_with_reward].copy()

        col1, col2 = st.columns(2)

        with col1:
            # Reward histogram
            fig_hist = px.histogram(reward_df, x='actual_reward',
                                  title='Reward Distribution',
                                  labels={'actual_reward': 'Reward Score'},
                                  nbins=20)
            fig_hist.add_vline(x=0, line_dash="dash", line_color="red",
                             annotation_text="Break-even")
            st.plotly_chart(fig_hist)

        with col2:
            # Cumulative reward over time
            reward_df = reward_df.sort_values('timestamp')
            reward_df['cumulative_reward'] = reward_df['actual_reward'].cumsum()

            fig_cum = px.line(reward_df, x='timestamp', y='cumulative_reward',
                            title='Cumulative Reward Over Time',
                            labels={'cumulative_reward': 'Cumulative Reward'})
            st.plotly_chart(fig_cum)

        # Reward vs Spread scatter plot
        st.subheader("Reward vs Signal Strength")
        fig_scatter = px.scatter(reward_df, x='spread', y='actual_reward',
                               title='Reward vs Spread Percentage',
                               labels={'spread': 'Spread %', 'actual_reward': 'Reward'},
                               trendline="ols")
        st.plotly_chart(fig_scatter)

    else:
        st.info("No signals with reward data yet. Reward calculation happens 5 minutes after signal generation.")

else:
    st.warning("No signals found in the database yet.")

# Refresh the page automatically
time.sleep(15)
st.rerun()