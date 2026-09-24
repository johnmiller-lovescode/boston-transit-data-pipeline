from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Boston Transit Analytics",
    page_icon=None,
    layout="wide",
)

DATA_FILE = Path(__file__).parent / "vehicle_positions.csv"

st.title("Boston Transit Analytics")
st.caption("MBTA vehicle position data processed through an AWS serverless data pipeline")

# Load Athena export
df = pd.read_csv(DATA_FILE)

# Ensure coordinates are numeric and remove unusable records
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df = df.dropna(subset=["latitude", "longitude"])



st.divider()

# Route filter
routes = sorted(df["route_id"].dropna().astype(str).unique())

selected_route = st.selectbox(
    "Filter by route",
    ["All Routes"] + routes,
)

if selected_route == "All Routes":
    filtered_df = df
else:
    filtered_df = df[df["route_id"].astype(str) == selected_route]

# Summary metrics for current selection
visible_vehicles = filtered_df["id"].nunique()
visible_routes = filtered_df["route_id"].nunique()

col1, col2 = st.columns(2)

with col1:
    st.metric("Vehicles", visible_vehicles)

with col2:
    st.metric("Routes", visible_routes)

st.divider()

st.subheader("Vehicles by Route")

route_counts = (
    df.groupby("route_id")["id"]
    .nunique()
    .sort_values(ascending=False)
    .head(15)
)

st.bar_chart(route_counts)

st.divider()

st.subheader("Vehicle Locations")

st.map(
    filtered_df,
    latitude="latitude",
    longitude="longitude",
    use_container_width=True,
)

st.caption(
    "Vehicle positions shown from MBTA data processed through "
    "Amazon S3, AWS Lambda, Apache Parquet, and Amazon Athena."
)

st.subheader("Vehicle Data")

display_columns = [
    "id",
    "route_id",
    "label",
    "current_status",
    "speed",
    "latitude",
    "longitude",
]

available_columns = [
    column for column in display_columns if column in df.columns
]

st.dataframe(
    filtered_df[available_columns],
    use_container_width=True,
    hide_index=True,
)