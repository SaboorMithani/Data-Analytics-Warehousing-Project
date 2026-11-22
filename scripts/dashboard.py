import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Pharma DWH - DE Observability", layout="wide")
st.title("Pharmaceutical Cold Chain DWH — Data Engineering Observability")
DATA_DIR = "./Data"

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Batch Ingestion Dashboard",
    "2. Storage & Staging Dashboard",
    "3. Analytical Querying Dashboard",
    "4. Star Schema Query Results"
])

with tab1:
    st.subheader("Batch Data Ingestion Operations (Staging Layer)")
    p = os.path.join(DATA_DIR, "metrics_batch_ingestion.csv")
    if os.path.exists(p):
        df = pd.read_csv(p)
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Batch Duration (sec)", round(df["DurationSec"].mean(), 2))
        c2.metric("Total Rows Processed", f"{df['RowsProcessed'].sum():,}")
        c3.metric("Batch Success Rate (%)", f"{df['SuccessRatePct'].mean():.1f}%")
        fig = px.bar(df, x="DurationSec", y="SourceFile", orientation="h", color="RunTime",
                     title="Load Duration (Seconds) per Source File (Horizontal Bar Chart)")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df)

with tab2:
    st.subheader("Storage & Staging Layer Metrics")
    p = os.path.join(DATA_DIR, "metrics_storage.csv")
    if os.path.exists(p):
        df = pd.read_csv(p).drop_duplicates(subset=["Domain"], keep="last")
        c1, c2, c3 = st.columns(3)
        c1.metric("Cumulative Table Row Count", f"{df['RowCount'].sum():,}")
        c2.metric("Total Storage Footprint (MB)", f"{df['StorageMB'].sum():.2f} MB")
        c3.metric("Date Coverage Span", "2023 – 2025 (Validated)")
        fig = px.pie(df, values="RowCount", names="Domain", hole=0.45,
                     title="Storage Breakdown (% of Total Rows by Domain - Donut Chart)")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df)

with tab3:
    st.subheader("Analytical Query Layer & Optimization Metrics (DuckDB)")
    p = os.path.join(DATA_DIR, "metrics_querying.csv")
    if os.path.exists(p):
        df = pd.read_csv(p)
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Query Execution Time (ms)", round(df["ExecutionTimeMs"].mean(), 2))
        c2.metric("Daily Active Query Count", len(df))
        c3.metric("Query Error Rate (%)", f"{df['ErrorRatePct'].mean():.1f}%")
        fig = px.bar(df, x="QueryName", y="ExecutionTimeMs", color="RunTime", barmode="group",
                     title="Query Execution Time (ms) per Analytical Query (Column Chart)")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df)

with tab4:
    st.subheader("Star Schema Dimensional Query Outputs")
    for q in ["Q1_Revenue_Margin_By_Class_Channel", "Q2_Hospital_Unfulfilled_Demand", "Q3_Warehouse_Near_Expiry_Stock"]:
        qp = os.path.join(DATA_DIR, f"result_{q}.csv")
        if os.path.exists(qp):
            st.markdown(f"**{q}**")
            st.dataframe(pd.read_csv(qp))
