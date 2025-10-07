import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Advanced Football Odds Dashboard", layout="wide")
st.title("⚽ Bet9ja Odds Movement & Comparison Dashboard")

uploaded_file = st.file_uploader("📥 Upload your Excel file with 'Initial' and 'Current' odds", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success(f"Loaded {len(df)} records.")

    # Convert to datetime for sorting
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.sort_values(by=["Match", "Market Type", "Option", "Timestamp"], inplace=True)

    # Filters
    st.sidebar.header("🔍 Filters")
    match_filter = st.sidebar.text_input("Filter by Match")
    market_filter = st.sidebar.text_input("Filter by Market Type")
    min_change = st.sidebar.slider("Minimum % Odds Change", 0, 100, 10)

    if match_filter:
        df = df[df["Match"].str.contains(match_filter, case=False)]
    if market_filter:
        df = df[df["Market Type"].str.contains(market_filter, case=False)]

    # Pivot to compare Initial vs Current odds
    pivot = df.pivot_table(
        index=["Match", "Market Type", "Option"],
        columns="Snapshot Type",
        values="Odds",
        aggfunc="first"
    ).reset_index()

    # Drop rows with missing data
    if "Initial" in pivot.columns and "Current" in pivot.columns:
        pivot.dropna(subset=["Initial", "Current"], inplace=True)
        pivot["Absolute Change"] = pivot["Current"] - pivot["Initial"]
        pivot["% Change"] = ((pivot["Current"] - pivot["Initial"]) / pivot["Initial"]) * 100
        pivot = pivot[pivot["% Change"].abs() >= min_change]

        st.subheader("📊 Odds Comparison Table")
        st.dataframe(pivot.style.format({
            "Initial": "{:.2f}",
            "Current": "{:.2f}",
            "% Change": "{:+.2f}%"
        }))

        # Top changes chart
        st.subheader("📈 Biggest Odds Shifts")
        chart_data = pivot.sort_values(by="% Change", ascending=False).head(10)
        fig = px.bar(
            chart_data,
            x="% Change",
            y="Match",
            color="Market Type",
            orientation="h",
            hover_data=["Option", "Initial", "Current"],
            title="Top 10 Odds Movements"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("❗ Please make sure your data includes both 'Initial' and 'Current' snapshots.")
else:
    st.info("⬆️ Upload a Bet9ja Excel file with both 'Initial' and 'Current' odds to begin.")
