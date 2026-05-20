import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from shared import uploader_and_load, time_since
from utils.styles import load_css

st.set_page_config(page_title="Top Songs", layout="wide")
load_css()


def compute_top_songs(df: pd.DataFrame, year: str | None, metric: str, n: int = 10) -> pd.DataFrame:
    filtered = df if year == "All Time" else df[df["year"] == int(year)]
    grouped = (
        filtered.groupby(["spotify_track_uri", "master_metadata_track_name", "master_metadata_album_artist_name"])
        .agg(
            plays=("ts", "count"),
            minutes=("min_played", "sum"),
            first_listen=("ts", "min"),
            last_listen=("ts", "max"),
        )
        .reset_index()
        .rename(columns={
            "master_metadata_track_name": "track",
            "master_metadata_album_artist_name": "artist",
        })
    )
    grouped["minutes"] = grouped["minutes"].round(1)
    sort_col = "plays" if metric == "Play Count" else "minutes"
    return grouped.sort_values(sort_col, ascending=False).head(n).reset_index(drop=True)


def make_bar_chart(top_df: pd.DataFrame, metric: str) -> go.Figure:
    col = "plays" if metric == "Play Count" else "minutes"
    labels = top_df["track"] + "<br><sup>" + top_df["artist"] + "</sup>"
    fig = go.Figure(go.Bar(
        x=top_df[col][::-1],
        y=labels[::-1],
        orientation="h",
        marker_color="#22c55e",
        text=top_df[col][::-1],
        textposition="outside",
        textfont_color="#ffffff",
    ))
    fig.update_layout(
        height=420,
        margin=dict(l=0, r=60, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#ffffff",
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, color="#ffffff"),
    )
    return fig


# ── UI ──────────────────────────────────────────────────────────────────────

st.title("Top Songs")

df = uploader_and_load()
if df is None:
    st.stop()

years = ["All Time"] + sorted(df["year"].unique().tolist(), reverse=True)

col1, col2 = st.columns([2, 2])
with col1:
    year = st.selectbox("Time Period", years)
with col2:
    metric = st.selectbox("Rank By", ["Play Count", "Minutes Listened"])

top_df = compute_top_songs(df, year, metric)

st.plotly_chart(make_bar_chart(top_df, metric), use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

for i, row in top_df.iterrows():
    rank = i + 1
    col_rank, col_info, col_stats = st.columns([1, 6, 4])

    with col_rank:
        color = ["#facc15", "#c0c0c0", "#cd7f32"][i] if i < 3 else "#444444"
        st.markdown(
            f"<div style='font-size:2.5rem; font-weight:700; color:{color}; text-align:center; padding-top:0.5rem;'>"
            f"#{rank}</div>",
            unsafe_allow_html=True,
        )

    with col_info:
        st.markdown(
            f"<p style='font-size:1.25rem; font-weight:700; margin:0;'>{row['track']}</p>"
            f"<p style='font-size:1rem; color:#888888; margin:0;'>{row['artist']}</p>"
            f"<p style='font-size:0.85rem; color:#555555; margin-top:0.25rem;'>"
            f"First heard {time_since(row['first_listen'])} ago · "
            f"Last played {row['last_listen'].strftime('%b %d, %Y')}"
            f"</p>",
            unsafe_allow_html=True,
        )

    with col_stats:
        m1, m2 = st.columns(2)
        m1.metric("Plays", f"{row['plays']:,}")
        m2.metric("Minutes", f"{row['minutes']:,.1f}")

    st.markdown("<hr>", unsafe_allow_html=True)
