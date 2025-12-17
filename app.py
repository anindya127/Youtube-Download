import streamlit as st
import yt_dlp
import os
import pandas as pd

# 1. Setup Directories
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

st.set_page_config(page_title="Ultra HD Downloader", page_icon="🚀", layout="wide")
st.title("🚀 YouTube Downloader (Smart Fallback)")

# 2. Cookie Setup
COOKIE_FILE = "cookies.txt"
if os.path.exists(COOKIE_FILE):
    COOKIE_PATH = os.path.abspath(COOKIE_FILE)
    use_cookies = True
    st.success("✅ Cookies found! Premium/4K/8K unlocked.")
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
                # STRICT ARGS: We must use the exact same args for analysis and download
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
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

# 4. Display & Download
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if info.get('thumbnail'):
            st.image(info.get('thumbnail'), width="stretch")
    with col2:
        st.subheader(info.get('title'))
        st.write(f"**Duration:** {info.get('duration_string')}")

    # --- PROCESS FORMATS ---
    formats = info.get('formats', [])
    video_options = []
    seen = set()
    
    for f in formats:
        if f.get('vcodec') != 'none':
            h = f.get('height') or 0
            fps = f.get('fps') or 0
            f_id = f.get('format_id')
            ext = f.get('ext')
            
            res_label = f"{h}p" if h else "Unknown"
            if h >= 2160: res_label += " (4K)"
            elif h >= 1440: res_label += " (2K)"
            elif h >= 1080: res_label += " (HD)"
            else: res_label += " (SD)"
            
            label = f"{res_label} | {fps}fps | {ext.upper()}"
            
            # Key to avoid duplicates
            key = f"{h}-{fps}"
            if key not in seen:
                seen.add(key)
                # Sort: Height > FPS
                sort_val = (h * 100) + fps
                video_options.append((sort_val, label, f_id, h))

    video_options.sort(key=lambda x: x[0], reverse=True)

    # --- SHOW OPTIONS ---
    st.write("### ⬇️ Download Options")
    
    # Selection Menu
    selected_tuple = st.selectbox(
        "Select Quality:", 
        video_options,
        format_func=lambda x: x[1]
    )
    
    if st.button("🚀 Start Download"):
        target_id = selected_tuple[2] # Format ID
        target_height = selected_tuple[3] # Resolution Height
        
        with st.spinner("Processing... (Auto-retrying if 4K fails)"):
            try:
                # Clear previous files
                for f in os.listdir(DOWNLOAD_FOLDER):
                    os.remove(os.path.join(DOWNLOAD_FOLDER, f))

                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"
                
                # Base Options
                base_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    'extractor_args': {'youtube': {'player_client': ['web', 'android']}},
                    # IMPORTANT: Use MKV to allow 4K VP9 video to merge with Opus audio
                    'merge_output_format': 'mkv' 
                }
                if use_cookies:
                    base_opts['cookiefile'] = COOKIE_PATH

                # --- RETRY STRATEGY ---
                success = False
                
                # ATTEMPT 1: Exact Format ID
                if not success:
                    try:
                        st.write("Attempt 1: Trying exact format match...")
                        opts = base_opts.copy()
                        opts['format'] = f"{target_id}+bestaudio/best"
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            ydl.download([url])
                        success = True
                    except Exception as e:
                        st.warning(f"Attempt 1 failed: {e}")

                # ATTEMPT 2: By Resolution (Strict)
                if not success:
                    try:
                        st.write(f"Attempt 2: Trying best video at {target_height}p...")
                        opts = base_opts.copy()
                        # "bestvideo[height=2160]+bestaudio"
                        opts['format'] = f"bestvideo[height={target_height}]+bestaudio/best"
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            ydl.download([url])
                        success = True
                    except Exception as e:
                        st.warning(f"Attempt 2 failed: {e}")

                # ATTEMPT 3: Best Available (Fallback)
                if not success:
                    try:
                        st.write("Attempt 3: Falling back to best available quality...")
                        opts = base_opts.copy()
                        opts['format'] = "bestvideo+bestaudio/best"
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            ydl.download([url])
                        success = True
                    except Exception as e:
                        st.error(f"All attempts failed: {e}")

                # --- SERVE FILE ---
                if success:
                    downloaded_file = None
                    for f in os.listdir(DOWNLOAD_FOLDER):
                        if f.startswith(safe_filename):
                            downloaded_file = os.path.join(DOWNLOAD_FOLDER, f)
                            final_ext = f.split('.')[-1]
                            break
                    
                    if downloaded_file:
                        st.success(f"✅ Downloaded successfully as .{final_ext.upper()}!")
                        with open(downloaded_file, "rb") as file:
                            st.download_button(
                                label=f"📥 Save {final_ext.upper()} to Device",
                                data=file,
                                file_name=f"{info['title']}.{final_ext}",
                                mime="application/octet-stream"
                            )
            except Exception as e:
                st.error(f"Critical Error: {e}")