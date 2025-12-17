import streamlit as st
import yt_dlp
import os
import pandas as pd

# 1. Setup Directories & Config
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

st.set_page_config(page_title="Ultra HD Downloader", page_icon="🚀", layout="wide")
st.title("🚀 YouTube Downloader (8K/4K Supported)")

# Check for cookies in the repository
COOKIE_FILE = "cookies.txt"
use_cookies = os.path.exists(COOKIE_FILE)

if use_cookies:
    st.success("✅ Cookies found! Premium/4K/8K formats unlocked.")
else:
    st.warning("⚠️ No cookies found. 4K might be restricted.")

# 2. URL Input
url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("🔍 Analyze Video"):
        with st.spinner("Decrypting video signature..."):
            try:
                # 'web' client is prioritized for 4K/8K
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'check_formats': True,
                    'extractor_args': {'youtube': {'player_client': ['web', 'android']}}
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_FILE

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.toast(f"Loaded: {info.get('title')}", icon="✅")

            except Exception as e:
                st.error(f"Error fetching info: {e}")

# 3. Display Options & Download
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if info.get('thumbnail'):
            st.image(info.get('thumbnail'), width="stretch")
    with col2:
        st.subheader(info.get('title'))
        st.write(f"**Channel:** {info.get('uploader')}")
        st.write(f"**Duration:** {info.get('duration_string')}")

    # --- PROCESS FORMATS ---
    formats = info.get('formats', [])
    video_options = []
    seen_resolutions = set()
    
    for f in formats:
        if f.get('vcodec') != 'none':
            height = f.get('height') or 0
            fps = f.get('fps') or 0
            
            # Label the resolution clearly
            res_label = f"{height}p" if height else "Unknown"
            if height >= 2160: res_label += " (4K/8K)"
            elif height >= 1440: res_label += " (2K)"
            elif height == 1080: res_label += " (FHD)"

            # We use height + fps as the unique key instead of Format ID
            full_label = f"{res_label} | {fps}fps"
            
            # Avoid duplicates in the dropdown (show best FPS for each resolution)
            unique_key = f"{height}-{fps}"
            if unique_key not in seen_resolutions:
                seen_resolutions.add(unique_key)
                
                # Sort Key: Height -> FPS
                sort_key = (height * 100) + fps
                video_options.append((sort_key, full_label, height, fps))

    # SORT: Highest resolution first
    video_options.sort(key=lambda x: x[0], reverse=True)

    # --- TABLE DISPLAY ---
    # Just to show the user what we found
    st.write("### 📊 Available Resolutions")
    table_data = [{"Resolution": opt[1]} for opt in video_options]
    if table_data:
        st.dataframe(pd.DataFrame(table_data), hide_index=True, width="stretch")

    # --- SELECTION ---
    st.write("### ⬇️ Download Options")
    download_type = st.radio("Select Type:", ["Video (Auto-Merge Audio)", "Audio Only (MP3)"])

    selected_height = None
    selected_fps = None
    
    if download_type.startswith("Video"):
        selected_label_tuple = st.selectbox(
            "Select Quality:", 
            video_options,
            format_func=lambda x: x[1]
        )
        selected_height = selected_label_tuple[2]
        selected_fps = selected_label_tuple[3]

    # 4. Download Button
    if st.button("🚀 Start Download"):
        with st.spinner("Processing... 4K videos may take time."):
            try:
                # Cleanup old files
                for f in os.listdir(DOWNLOAD_FOLDER):
                    os.remove(os.path.join(DOWNLOAD_FOLDER, f))

                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"
                
                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    # We MUST use the same client args to find the 4K streams again
                    'extractor_args': {'youtube': {'player_client': ['web', 'android']}}
                }
                
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_FILE

                if "Audio" in download_type:
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                else:
                    # ROBUST LOGIC: Ask for the specific height instead of ID
                    # This prevents "Format Not Found" errors if IDs change
                    ydl_opts['format'] = f"bestvideo[height={selected_height}]+bestaudio/best[height={selected_height}]/best"
                    
                    # NOTE: We removed 'merge_output_format' = 'mp4' 
                    # This allows 4K to download as MKV/WebM (Native) which is safer.

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Find the file
                downloaded_file = None
                for f in os.listdir(DOWNLOAD_FOLDER):
                    if f.startswith(safe_filename):
                        downloaded_file = os.path.join(DOWNLOAD_FOLDER, f)
                        final_ext = f.split('.')[-1]
                        break
                
                if downloaded_file:
                    st.success("✅ Done! File ready.")
                    with open(downloaded_file, "rb") as file:
                        st.download_button(
                            label=f"📥 Save {final_ext.upper()}",
                            data=file,
                            file_name=f"{info['title']}.{final_ext}",
                            mime="application/octet-stream"
                        )
                else:
                    st.error("Processing failed.")

            except Exception as e:
                st.error(f"Error: {e}")