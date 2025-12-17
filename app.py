import streamlit as st
import yt_dlp
import os
import pandas as pd
import shutil

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Check for cookies (But we will be smart about when to use them)
COOKIE_FILE = "cookies.txt"
if os.path.exists(COOKIE_FILE):
    COOKIE_PATH = os.path.abspath(COOKIE_FILE)
    has_cookies = True
else:
    COOKIE_PATH = None
    has_cookies = False

st.set_page_config(page_title="Simple YouTube Downloader", layout="wide")
st.title("📺 YouTube Downloader (Stable Android Mode)")

# --- 1. INPUT ---
url = st.text_input("Paste YouTube URL:")

# --- 2. ANALYZE (Generate Table) ---
if url:
    if st.button("🔍 Analyze Video"):
        with st.spinner("Fetching video details..."):
            try:
                # FIX: We strictly use 'android' client because it is the most stable for Cloud.
                # CRITICAL FIX: We DO NOT pass cookies to Android client, or yt-dlp will skip it.
                ydl_opts = {
                    'quiet': True,
                    'extractor_args': {'youtube': {'player_client': ['android']}},
                }
                
                # We intentionally DO NOT add 'cookiefile' here to prevent the crash.

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.success(f"Loaded: {info.get('title')}")

            except Exception as e:
                st.error(f"Error: {e}")

# --- 3. DISPLAY TABLE & OPTIONS ---
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    
    # --- A. BUILD TABLE DATA ---
    formats = info.get('formats', [])
    table_rows = []
    
    for f in formats:
        # Filter for relevant formats (Video or Audio)
        if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
            f_id = f.get('format_id')
            ext = f.get('ext')
            res = f.get('resolution') if f.get('resolution') else "Audio Only"
            fps = f.get('fps') if f.get('fps') else "-"
            note = f.get('format_note') if f.get('format_note') else ""
            filesize = f.get('filesize') or f.get('filesize_approx')
            size_mb = f"{filesize / 1024 / 1024:.1f} MB" if filesize else "N/A"

            table_rows.append({
                "Format ID": f_id,
                "Resolution": res,
                "Extension": ext,
                "FPS": fps,
                "Note": note,
                "Size": size_mb,
                "_sort": f.get('height') or 0
            })

    # Sort & Display
    df = pd.DataFrame(table_rows)
    df = df.sort_values(by="_sort", ascending=False)
    
    st.write("### Available Resolutions")
    st.dataframe(
        df[["Format ID", "Resolution", "Extension", "FPS", "Note", "Size"]],
        hide_index=True,
        use_container_width=True
    )

    # --- B. DOWNLOAD OPTIONS ---
    st.write("### Download Options")
    
    dl_type = st.radio("Select Type:", ["Video (Auto-Merge Audio)", "Audio Only (MP3)"])
    
    # Dropdown Options
    options_list = []
    for index, row in df.iterrows():
        label = f"{row['Format ID']} - {row['Resolution']} ({row['Extension']})"
        options_list.append((label, row['Format ID']))
    
    selected_option = st.selectbox("Select Format ID:", options_list, format_func=lambda x: x[0])
    
    # --- C. EXECUTE DOWNLOAD ---
    if st.button("Start Download"):
        target_id = selected_option[1]
        
        with st.spinner("Downloading..."):
            try:
                # Cleanup
                if os.path.exists(DOWNLOAD_FOLDER):
                    shutil.rmtree(DOWNLOAD_FOLDER)
                os.makedirs(DOWNLOAD_FOLDER)
                
                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"

                # Setup Options
                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    'extractor_args': {'youtube': {'player_client': ['android']}}, # Strict Android
                }
                # CRITICAL FIX: Do NOT use cookies for video download either
                
                if dl_type == "Audio Only (MP3)":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }]
                else:
                    ydl_opts['format'] = f"{target_id}+bestaudio/best"
                    ydl_opts['merge_output_format'] = 'mkv'

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Find File
                found = False
                for f in os.listdir(DOWNLOAD_FOLDER):
                    if f.startswith(safe_filename):
                        filepath = os.path.join(DOWNLOAD_FOLDER, f)
                        final_name = f"{info['title']}.{f.split('.')[-1]}"
                        
                        st.success("Download Complete!")
                        with open(filepath, "rb") as file:
                            st.download_button(
                                label="📥 Save to Device",
                                data=file,
                                file_name=final_name,
                                mime="application/octet-stream"
                            )
                        found = True
                        break
                
                if not found:
                    st.error("Error: File not found.")

            except Exception as e:
                st.error(f"Download Error: {e}")