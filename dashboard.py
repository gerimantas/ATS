import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time

DB_URL = "sqlite:///ats.db"
engine = create_engine(DB_URL)

st.set_page_config(layout="wide")

@st.cache_data(ttl=10) # Cache data for 10 seconds
def load_data():
    try:
        query = "SELECT * FROM signals ORDER BY timestamp DESC LIMIT 100"
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
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Signals Logged (Last 100)", len(df))
    avg_spread = df['spread'].mean()
    col2.metric("Average Spread", f"{avg_spread:.4f}%")
    avg_latency = df['data_latency_ms'].mean()
    col3.metric("Average Latency (ms)", f"{avg_latency:.2f}")
    
    st.subheader("Latest Generated Signals")
    st.dataframe(df)
else:
    st.warning("No signals found in the database yet.")

# Refresh the page automatically
time.sleep(15)
st.rerun()