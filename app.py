import streamlit as st
import yt_dlp
import os
import pandas as pd

# 1. Setup Directories & Config
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Check for cookies in the repository
COOKIE_FILE = "cookies.txt"
use_cookies = os.path.exists(COOKIE_FILE)

st.set_page_config(page_title="Ultra HD Downloader", page_icon="🚀", layout="wide")
st.title("🚀 YouTube Downloader")

# Status Indicator
if use_cookies:
    st.success("Cookies found!")
else:
    st.warning("No cookies found. 4K might be restricted.")

# 2. URL Input
url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("🔍 Analyze Video"):
        with st.spinner("Decrypting video signature (this needs Node.js)..."):
            try:
                # We do NOT force a specific client here to ensure we get ALL formats (WebM + MP4)
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'check_formats': True, # Strict check to ensure links work
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
        st.image(info.get('thumbnail'), use_container_width=True)
    with col2:
        st.subheader(info.get('title'))
        st.write(f"**Channel:** {info.get('uploader')}")
        st.write(f"**Duration:** {info.get('duration_string')}")

    # --- PROCESS FORMATS ---
    formats = info.get('formats', [])
    video_options = []
    
    for f in formats:
        # Filter: Must be video, not a dummy stream, and not an m3u8 (HLS) duplicate if possible
        if f.get('vcodec') != 'none':
            f_id = f.get('format_id')
            ext = f.get('ext')
            width = f.get('width') or 0
            height = f.get('height') or 0
            note = f.get('format_note', '')
            fps = f.get('fps')
            
            # Label the resolution clearly
            res_label = f"{height}p" if height else "Unknown"
            if height >= 2160: res_label += " (4K/8K)"
            elif height >= 1440: res_label += " (2K)"
            elif height == 1080: res_label += " (FHD)"

            # Create a label for the dropdown
            full_label = f"{res_label} | {ext.upper()} | {fps}fps | ID: {f_id}"
            
            # Store tuple: (Sort Key, Label, Format ID)
            # Sort Key = Height (Primary) + FPS (Secondary)
            sort_key = (height if height else 0) * 100 + (fps if fps else 0)
            video_options.append((sort_key, full_label, f_id, height, ext))

    # SORT: Highest resolution first
    video_options.sort(key=lambda x: x[0], reverse=True)

    # --- TABLE DISPLAY ---
    st.write("###Available Resolutions")
    
    table_data = []
    for _, label, f_id, h, ext in video_options:
        table_data.append({
            "Resolution": f"{h}p",
            "Format": ext.upper(),
            "Label": label,
            "ID": f_id
        })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df[["Resolution", "Format", "ID"]], use_container_width=True)

    # --- SELECTION ---
    st.write("### ⬇️ Download Options")
    download_type = st.radio("Select Type:", ["Video (Auto-Merge Audio)", "Audio Only (MP3)"])

    selected_format_id = None
    
    if download_type.startswith("Video"):
        # Dropdown uses the sorted list
        selected_label_tuple = st.selectbox(
            "Select Quality:", 
            video_options,
            format_func=lambda x: x[1] # Show the label part of the tuple
        )
        selected_format_id = selected_label_tuple[2] # Get the ID

    # 4. Download Button
    if st.button("Start Download"):
        with st.spinner("Processing..."):
            try:
                # Cleanup old files
                for f in os.listdir(DOWNLOAD_FOLDER):
                    os.remove(os.path.join(DOWNLOAD_FOLDER, f))

                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"
                
                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    # This ensures we don't get stuck on one client
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
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
                    # VIDEO: Download specific ID + Best Audio and Merge
                    ydl_opts['format'] = f"{selected_format_id}+bestaudio/best"
                    ydl_opts['merge_output_format'] = 'mp4' 

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
                    st.success("✅ Done!")
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