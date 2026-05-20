import os
import io
import json
import zipfile
from datetime import timezone
import pandas as pd
import streamlit as st


def time_since(ts) -> str:
    now = pd.Timestamp.now(tz=timezone.utc)
    days_total = (now - ts).days
    years = days_total // 365
    days = days_total % 365
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    return " and ".join(parts) if parts else "today"


def uploader_and_load() -> pd.DataFrame | None:
    st.sidebar.markdown("### Upload Your Spotify Data")

    # If a file was previously uploaded this session, skip the uploader and use stored bytes.
    if "zip_bytes" in st.session_state:
        st.sidebar.caption(f"Loaded: {st.session_state['zip_name']}")
        if st.sidebar.button("Clear data"):
            for key in ("zip_bytes", "zip_name", "zip_size"):
                st.session_state.pop(key, None)
            st.rerun()
        return _load(st.session_state["zip_bytes"])

    st.sidebar.markdown(
        "- Zip your Spotify data folder titled 'Spotify Extended Streaming History' and upload it here. "
        "\n"
        "- [Download your Spotify data ->](https://www.spotify.com/us/account/privacy/)"
        "\n"
        "- [More info on downloading your Spotify data ->](https://support.spotify.com/article/data-rights-and-privacy-settings/)"
    )
    zipped = st.sidebar.file_uploader(
        "Select zip file",
        type="zip",
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    if zipped is None:
        st.info("Zip your Spotify data folder and upload it in the sidebar to get started.")
        return None

    st.session_state["zip_name"] = zipped.name
    st.session_state["zip_size"] = zipped.size
    st.session_state["zip_bytes"] = zipped.read()
    return _load(st.session_state["zip_bytes"])

@st.cache_data
def _load(zip_bytes: bytes) -> pd.DataFrame:
    records = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        json_files = [
            name for name in zf.namelist()
            if os.path.basename(name).startswith("Streaming_History_Audio")
            and name.endswith(".json")
            and not os.path.basename(name).startswith(".")  # skip macOS junk
        ]
        if not json_files:
            st.error("No Streaming_History_Audio*.json files found in the zip.")
            st.stop()
        for name in sorted(json_files):
            with zf.open(name) as f:
                records.extend(json.load(f))

    df = pd.DataFrame(records)
    df = df[df["master_metadata_track_name"].notna()].copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["month_start"] = df["ts"].dt.to_period("M").dt.to_timestamp()
    df["year"] = df["ts"].dt.year
    df["min_played"] = df["ms_played"] / 60_000
    return df