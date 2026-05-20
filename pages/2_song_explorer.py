import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from shared import uploader_and_load, time_since
from utils.styles import load_css

st.set_page_config(page_title="Song Explorer", layout="wide")
load_css()


@st.cache_data
def build_options(df: pd.DataFrame) -> list[str]:
    return (
        df[["master_metadata_track_name", "master_metadata_album_artist_name"]]
        .drop_duplicates()
        .sort_values(["master_metadata_album_artist_name", "master_metadata_track_name"])
        .apply(lambda r: f"{r['master_metadata_track_name']} — {r['master_metadata_album_artist_name']}", axis=1)
        .tolist()
    )


def make_chart(track_df: pd.DataFrame) -> go.Figure:
    first_month = track_df["month_start"].min()
    monthly = (
        track_df.groupby("month_start")
        .agg(plays=("ts", "count"))
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["month_start"], y=monthly["plays"],
        name="Plays", marker_color="#22c55e",
    ))
    fig.add_vline(
        x=first_month.timestamp() * 1000,
        line_dash="dash", line_color="#facc15",
        annotation_text=f"First listen: {track_df['ts'].min().strftime('%b %d, %Y')}",
        annotation_position="top right",
        annotation_font_color="#facc15",
    )
    fig.update_layout(
        title="Plays per Month",
        height=400,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#ffffff",
    )
    fig.update_xaxes(showgrid=False, color="#888888")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", color="#888888")

    return fig


# ── UI ──────────────────────────────────────────────────────────────────────

st.title("Song Explorer")

df = uploader_and_load()
if df is None:
    st.stop()

options = build_options(df)

selected = st.selectbox(
    "Search by song or artist",
    options,
    index=None,
    placeholder="Type to search...",
)

if selected:
    track_name, artist_name = selected.split(" — ", 1)
    track_df = df[
        (df["master_metadata_track_name"] == track_name) &
        (df["master_metadata_album_artist_name"] == artist_name)
    ]

    first_listen = track_df["ts"].min()
    total_minutes = track_df["min_played"].sum()
    total_plays = len(track_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Plays", f"{total_plays:,}")
    col2.metric("Total Minutes", f"{total_minutes:.1f}")
    col3.metric("First Listen", first_listen.strftime("%b %d, %Y"))

    st.plotly_chart(make_chart(track_df), use_container_width=True)

    st.markdown(
        f"<p style='font-size:1.1rem; color:#888888;'>"
        f"You first discovered <strong style='color:#ffffff'>{track_name}</strong> "
        f"by <strong style='color:#ffffff'>{artist_name}</strong> "
        f"<strong style='color:#22c55e'>{time_since(first_listen)}</strong> ago."
        f"</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<p style='font-size:3rem; font-weight:700; margin:0.25rem 0;'>"
        f"{total_minutes:.0f} <span style='font-size:1.5rem; font-weight:400; color:#888888;'>minutes listened</span>"
        f"</p>",
        unsafe_allow_html=True,
    )

    with st.expander("Raw stream records"):
        st.dataframe(
            track_df[["ts", "min_played", "platform", "shuffle", "skipped", "reason_end"]]
            .sort_values("ts", ascending=False)
            .reset_index(drop=True)
        )
