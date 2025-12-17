import streamlit as st
import yt_dlp
import os
import pandas as pd
import shutil

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Cookie Setup (Still good to have, even for Android client)
COOKIE_FILE = "cookies.txt"
if os.path.exists(COOKIE_FILE):
    COOKIE_PATH = os.path.abspath(COOKIE_FILE)
    use_cookies = True
else:
    COOKIE_PATH = None
    use_cookies = False

st.set_page_config(page_title="Simple YouTube Downloader", layout="wide")
st.title("📺 YouTube Downloader (Table View)")

# --- 1. INPUT ---
url = st.text_input("Paste YouTube URL:")

# --- 2. ANALYZE (Generate Table) ---
if url:
    if st.button("🔍 Analyze Video"):
        with st.spinner("Fetching video details..."):
            try:
                # We use 'android' client because you confirmed Web/iOS failed.
                # Android is the most stable for Cloud Servers (usually max 1080p).
                ydl_opts = {
                    'quiet': True,
                    'extractor_args': {'youtube': {'player_client': ['android']}},
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

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

            # Create the row for the UI table
            table_rows.append({
                "Format ID": f_id,
                "Resolution": res,
                "Extension": ext,
                "FPS": fps,
                "Note": note,
                "Size": size_mb,
                "_sort": f.get('height') or 0 # Hidden column for sorting
            })

    # Convert to DataFrame
    df = pd.DataFrame(table_rows)
    # Sort by Resolution (High to Low)
    df = df.sort_values(by="_sort", ascending=False)
    
    # Display the Table (Matches your screenshot design)
    st.write("### Available Resolutions")
    st.dataframe(
        df[["Format ID", "Resolution", "Extension", "FPS", "Note", "Size"]],
        hide_index=True,
        use_container_width=True
    )

    # --- B. DOWNLOAD OPTIONS ---
    st.write("### Download Options")
    
    # 1. Select Type
    dl_type = st.radio("Select Type:", ["Video (Auto-Merge Audio)", "Audio Only (MP3)"])
    
    # 2. Select Format ID (Dropdown populated from table)
    # We create a list of labels for the dropdown
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
                # Cleanup old files
                if os.path.exists(DOWNLOAD_FOLDER):
                    shutil.rmtree(DOWNLOAD_FOLDER)
                os.makedirs(DOWNLOAD_FOLDER)
                
                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"

                # Setup Options
                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    'extractor_args': {'youtube': {'player_client': ['android']}}, # Stick to Android
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                # Logic based on user selection
                if dl_type == "Audio Only (MP3)":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }]
                else:
                    # VIDEO: Match the exact ID user picked + Best Audio
                    ydl_opts['format'] = f"{target_id}+bestaudio/best"
                    # We use MKV because it is safer for merging than MP4 on servers
                    ydl_opts['merge_output_format'] = 'mkv'

                # Run Download
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Find File and Show Button
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