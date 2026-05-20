import streamlit as st
from utils.styles import load_css
from shared import uploader_and_load

st.set_page_config(
    page_title="Your Music",
    layout="wide",
)

load_css()

st.markdown(
    "<div class='hero'>"
    "<h1>Your Music</h1>"
    "<p>Explore your complete Spotify listening history — search songs, discover trends, and see your all-time charts.</p>"
    "</div>",
    unsafe_allow_html=True,
)

df = uploader_and_load()
if df is None:
    st.stop()

total_plays = len(df)
total_minutes = df["min_played"].sum()
unique_tracks = df["master_metadata_track_name"].nunique()
unique_artists = df["master_metadata_album_artist_name"].nunique()
years_span = df["year"].max() - df["year"].min() + 1

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Plays", f"{total_plays:,}")
col2.metric("Minutes Listened", f"{total_minutes:,.0f}")
col3.metric("Unique Tracks", f"{unique_tracks:,}")
col4.metric("Unique Artists", f"{unique_artists:,}")
col5.metric("Years of History", f"{years_span}")
