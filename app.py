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

# 2. Robust Cookie Handling (Use Absolute Path)
COOKIE_FILE = "cookies.txt"
if os.path.exists(COOKIE_FILE):
    COOKIE_PATH = os.path.abspath(COOKIE_FILE)
    use_cookies = True
    st.success("✅ Cookies found! Premium/4K/8K formats unlocked.")
else:
    COOKIE_PATH = None
    use_cookies = False
    st.warning("⚠️ No cookies found. 4K might be restricted.")

# 3. URL Input
url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("🔍 Analyze Video"):
        with st.spinner("Decrypting video signature..."):
            try:
                # Analysis Options
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'check_formats': True,
                    # Ensure we see 4K (Web Client)
                    'extractor_args': {'youtube': {'player_client': ['web', 'android']}}
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.toast(f"Loaded: {info.get('title')}", icon="✅")

            except Exception as e:
                st.error(f"Error fetching info: {e}")

# 4. Display Options & Download
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
            
            res_label = f"{height}p" if height else "Unknown"
            if height >= 2160: res_label += " (4K/8K)"
            elif height >= 1440: res_label += " (2K)"
            elif height == 1080: res_label += " (FHD)"

            full_label = f"{res_label} | {fps}fps"
            
            # Deduplicate
            unique_key = f"{height}-{fps}"
            if unique_key not in seen_resolutions:
                seen_resolutions.add(unique_key)
                # Sort Key: Height -> FPS
                sort_key = (height * 100) + fps
                video_options.append((sort_key, full_label, height, fps))

    # Sort High to Low
    video_options.sort(key=lambda x: x[0], reverse=True)

    # --- SHOW TABLE ---
    st.write("### 📊 Available Resolutions")
    table_data = [{"Resolution": opt[1]} for opt in video_options]
    if table_data:
        st.dataframe(pd.DataFrame(table_data), hide_index=True, width="stretch")

    # --- SELECTION ---
    st.write("### ⬇️ Download Options")
    download_type = st.radio("Select Type:", ["Video (Auto-Merge Audio)", "Audio Only (MP3)"])

    selected_height = None
    
    if download_type.startswith("Video"):
        selected_label_tuple = st.selectbox(
            "Select Quality:", 
            video_options,
            format_func=lambda x: x[1]
        )
        selected_height = selected_label_tuple[2] # We only need height for sorting

    # 5. Download Button
    if st.button("🚀 Start Download"):
        with st.spinner("Processing... (This may take a moment)"):
            try:
                # Cleanup
                for f in os.listdir(DOWNLOAD_FOLDER):
                    os.remove(os.path.join(DOWNLOAD_FOLDER, f))

                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"
                
                # --- ROBUST DOWNLOAD CONFIGURATION ---
                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    # Prioritize Web client for 4K
                    'extractor_args': {'youtube': {'player_client': ['web', 'android']}},
                }
                
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                if "Audio" in download_type:
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                else:
                    # THE FIX: Use Format Sorting instead of Strict Format Selection
                    # This prevents "Requested format not available" crashes
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                    ydl_opts['format_sort'] = [f'res:{selected_height}'] 
                    
                    # Explain: The line above tells yt-dlp: 
                    # "Get the best video, but prioritize the resolution I selected."

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Find result
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
                    st.error("Processing failed: No file found.")

            except Exception as e:
                st.error(f"Error: {e}")