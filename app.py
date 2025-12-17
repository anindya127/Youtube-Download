import streamlit as st
import yt_dlp
import os
import pandas as pd
import shutil

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# NOTE: We intentionally DO NOT load cookies.txt here.
# The Android client (which works best on Cloud) crashes if cookies are provided.
# This ensures the app remains stable for sharing.

st.set_page_config(page_title="Friend's Downloader", page_icon="🔗", layout="wide")
st.title("🔗 YouTube Downloader (Shareable Version)")

# --- 1. INPUT ---
url = st.text_input("Paste YouTube URL here:")

# --- 2. ANALYZE (Generate Table) ---
if url:
    if st.button("🔍 Analyze Video"):
        with st.spinner("Connecting to YouTube..."):
            try:
                # We use the 'android' client. 
                # It is the only one that reliably works on free Cloud servers (up to 1080p).
                ydl_opts = {
                    'quiet': True,
                    'extractor_args': {'youtube': {'player_client': ['android']}},
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.success(f"Found: {info.get('title')}")

            except Exception as e:
                st.error(f"Could not fetch video. YouTube might be blocking the server temporarily.\nError: {e}")

# --- 3. DISPLAY TABLE & OPTIONS ---
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    
    st.write(f"**Title:** {info.get('title')}")

    # --- A. BUILD TABLE DATA ---
    formats = info.get('formats', [])
    table_rows = []
    
    for f in formats:
        # Filter for relevant formats
        if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
            f_id = f.get('format_id')
            ext = f.get('ext')
            res = f.get('resolution') if f.get('resolution') else "Audio Only"
            fps = f.get('fps') if f.get('fps') else "-"
            note = f.get('format_note') or ""
            filesize = f.get('filesize') or f.get('filesize_approx')
            size_mb = f"{filesize / 1024 / 1024:.1f} MB" if filesize else "--"

            # We use a hidden sort key to put higher resolution at top
            height = f.get('height') or 0
            
            table_rows.append({
                "ID": f_id,
                "Resolution": res,
                "Ext": ext,
                "FPS": fps,
                "Size": size_mb,
                "Note": note,
                "_sort": height
            })

    # Sort & Display
    df = pd.DataFrame(table_rows)
    df = df.sort_values(by="_sort", ascending=False)
    
    st.write("### 📊 Available Qualities")
    st.dataframe(
        df[["ID", "Resolution", "Ext", "FPS", "Size", "Note"]],
        hide_index=True,
        use_container_width=True
    )

    # --- B. DOWNLOAD OPTIONS ---
    st.write("### ⬇️ Download Options")
    
    dl_type = st.radio("Select Type:", ["Video (Auto-Merge Audio)", "Audio Only (MP3)"])
    
    # Dropdown Options
    options_list = []
    for index, row in df.iterrows():
        label = f"{row['Resolution']} | {row['FPS']}fps | {row['Ext']} (ID: {row['ID']})"
        options_list.append((label, row['ID']))
    
    selected_option = st.selectbox("Select Quality to Download:", options_list, format_func=