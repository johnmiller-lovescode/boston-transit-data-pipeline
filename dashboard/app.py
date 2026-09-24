from pathlib import Path

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

st.set_page_config(
    page_title="Boston Transit Analytics",
    page_icon=None,
    layout="wide",
)

DATA_FILE = Path(__file__).parent / "vehicle_positions.csv"

@st.cache_data
def get_route_info(route_ids):
    route_info = {}

    for route_id in route_ids:
        route_id = str(route_id)

        try:
            response = requests.get(
                f"https://api-v3.mbta.com/routes/{route_id}",
                timeout=5,
            )
            response.raise_for_status()

            attributes = response.json()["data"]["attributes"]

            short_name = attributes.get("short_name") or route_id
            long_name = attributes.get("long_name") or ""
            hex_color = attributes.get("color") or "0078D4"

            # Friendly display name
            if long_name and long_name != short_name:
                display_name = f"{short_name} — {long_name}"
            else:
                display_name = short_name

            # Convert MBTA hex color to RGB for PyDeck
            hex_color = hex_color.lstrip("#")
            rgb = [
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
                220,
            ]

            route_info[route_id] = {
                "name": display_name,
                "color": rgb,
            }

        except Exception:
            route_info[route_id] = {
                "name": route_id,
                "color": [0, 120, 212, 220],
            }

    return route_info

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

route_info = get_route_info(tuple(routes))

selected_route = st.selectbox(
    "Filter by route",
    ["All Routes"] + routes,
    format_func=lambda route: (
        "All Routes"
        if route == "All Routes"
        else route_info.get(route, {}).get("name", route)
    ),
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

map_df = filtered_df.copy()

map_df["status_display"] = (
    map_df["current_status"]
    .fillna("Not reported")
    .astype(str)
    .str.replace("_", " ", regex=False)
    .str.title()
)

map_df["speed_display"] = map_df["speed"].apply(
    lambda x: "Not reported" if pd.isna(x) else str(x)
)


map_df["route_name"] = map_df["route_id"].astype(str).map(
    lambda route: route_info.get(route, {}).get("name", route)
)

map_df["color"] = map_df["route_id"].astype(str).map(
    lambda route: route_info.get(route, {}).get(
        "color",
        [0, 120, 212, 220],
    )
)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position="[longitude, latitude]",
    get_fill_color="color",
    get_radius=80,
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=map_df["latitude"].mean(),
    longitude=map_df["longitude"].mean(),
    zoom=10,
    pitch=0,
)

map_df["status_display"] = (
    map_df["current_status"]
    .fillna("Not reported")
    .str.replace("_", " ", regex=False)
    .str.title()
)

map_df["speed_display"] = map_df["speed"].apply(
    lambda speed: "Not reported"
    if pd.isna(speed)
    else f"{speed:g}"
)

tooltip = {
    "html": """
        <b>{route_name}</b><br/>
        <b>Vehicle:</b> {label}<br/>
        <b>Status:</b> {status_display}<br/>
        <b>Speed:</b> {speed_display}
    """,
    "style": {
        "backgroundColor": "#111827",
        "color": "white",
    },
}

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style="dark",
)

st.pydeck_chart(deck, use_container_width=True)

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

table_df = filtered_df[available_columns].copy()

table_df["route_id"] = table_df["route_id"].astype(str).map(
    lambda route: route_info.get(route, {}).get("name", route)
)

table_df["current_status"] = (
    table_df["current_status"]
    .fillna("Not reported")
    .astype(str)
    .str.replace("_", " ", regex=False)
    .str.title()
)

table_df["speed"] = table_df["speed"].apply(
    lambda speed: "Not reported" if pd.isna(speed) else speed
)

table_df = table_df.rename(
    columns={
        "id": "Vehicle ID",
        "route_id": "Route",
        "label": "Vehicle",
        "current_status": "Status",
        "speed": "Speed",
        "latitude": "Latitude",
        "longitude": "Longitude",
    }
)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
)