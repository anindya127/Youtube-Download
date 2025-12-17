import streamlit as st
import yt_dlp
import os
import pandas as pd
import shutil

# 1. Setup
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

st.set_page_config(page_title="Universal Downloader", page_icon="🛠️", layout="wide")
st.title("🛠️ YouTube Downloader (Connection Manager)")

# 2. Check System Tools (Debug Info)
col1, col2 = st.columns(2)
with col1:
    if shutil.which("ffmpeg"):
        st.success("✅ FFmpeg is installed")
    else:
        st.error("❌ FFmpeg NOT found (Merges will fail)")
with col2:
    if shutil.which("node"):
        st.success("✅ Node.js is installed")
    else:
        st.warning("⚠️ Node.js NOT found (4K might fail)")

# 3. Cookie Setup
COOKIE_FILE = "cookies.txt"
if os.path.exists(COOKIE_FILE):
    COOKIE_PATH = os.path.abspath(COOKIE_FILE)
    use_cookies = True
    st.info("🍪 Cookies.txt detected & active.")
else:
    COOKIE_PATH = None
    use_cookies = False

# 4. Connection Settings
st.write("### ⚙️ Connection Settings")
client_mode = st.selectbox(
    "Select Connection Mode (Try switching if analysis fails):",
    [
        "4K/8K Mode (Web Client) - Best Quality, Higher Block Risk",
        "Safe Mode (Android Client) - Reliable, Max 1080p",
        "Legacy Mode (iOS Client) - Alternative Backup"
    ]
)

# Map selection to yt-dlp args
if "Android" in client_mode:
    client_args = {'player_client': ['android']}
elif "iOS" in client_mode:
    client_args = {'player_client': ['ios']}
else:
    client_args = {'player_client': ['web', 'android']} # Default 4K attempt

# 5. URL Input
url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("🔍 Analyze Video"):
        with st.spinner("Connecting to YouTube..."):
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {'youtube': client_args},
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.toast("Analysis Successful!", icon="✅")

            except Exception as e:
                st.error(f"Analysis Failed: {e}")
                st.write("👉 **Tip:** Try changing the 'Connection Mode' dropdown above to **Safe Mode (Android)**.")

# 6. Display & Download
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    
    st.divider()
    c1, c2 = st.columns([1, 2])
    with c1:
        if info.get('thumbnail'):
            st.image(info.get('thumbnail'), width="stretch")
    with c2:
        st.subheader(info.get('title'))
        st.write(f"**Duration:** {info.get('duration_string')}")

    # --- BUILD TABLE ---
    formats = info.get('formats', [])
    data_list = []
    
    for f in formats:
        # Filter junk
        if f.get('vcodec') == 'none' and f.get('acodec') == 'none': continue
        if 'storyboard' in (f.get('format_note') or ''): continue

        f_id = f.get('format_id')
        ext = f.get('ext')
        h = f.get('height')
        
        # Labeling
        if f.get('vcodec') != 'none':
            type_lbl = "Video"
            res_lbl = f"{h}p" if h else "Unknown"
            if h and h >= 2160: res_lbl += " 🌟"
            
            # Check Audio
            has_audio = "Yes" if f.get('acodec') != 'none' else "No (Merge Needed)"
        else:
            type_lbl = "Audio"
            res_lbl = "Audio Only"
            has_audio = "Yes"

        # Size
        fs = f.get('filesize') or f.get('filesize_approx')
        size_lbl = f"{fs / 1024 / 1024:.1f} MB" if fs else "--"

        data_list.append({
            "Label": f"{type_lbl} | {res_lbl} | {ext} | {has_audio}",
            "ID": f_id,
            "Type": type_lbl,
            "HasAudio": has_audio,
            "_sort": h if h else 0
        })

    # Sort & Display
    df = pd.DataFrame(data_list).sort_values(by="_sort", ascending=False)
    
    st.write("### ⬇️ Available Formats")
    
    # Dropdown
    selected_row = st.selectbox(
        "Select Format:",
        df.to_dict('records'),
        format_func=lambda x: x['Label']
    )

    if st.button("🚀 Download This Format"):
        target_id = selected_row['ID']
        has_audio = selected_row['HasAudio']
        type_lbl = selected_row['Type']

        with st.spinner("Downloading..."):
            try:
                # Cleanup
                for f in os.listdir(DOWNLOAD_FOLDER):
                    os.remove(os.path.join(DOWNLOAD_FOLDER, f))
                
                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"

                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    'extractor_args': {'youtube': client_args}, # MUST match analysis args
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                # --- DOWNLOAD LOGIC ---
                if type_lbl == "Audio":
                    ydl_opts['format'] = target_id
                    ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
                
                elif "Merge Needed" in has_audio:
                    # Video Only -> Merge with best audio
                    ydl_opts['format'] = f"{target_id}+bestaudio/best"
                    ydl_opts['merge_output_format'] = 'mkv' # Safest container
                
                else:
                    # Direct Download
                    ydl_opts['format'] = target_id

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Serve File
                found_file = None
                for f in os.listdir(DOWNLOAD_FOLDER):
                    if f.startswith(safe_filename):
                        found_file = os.path.join(DOWNLOAD_FOLDER, f)
                        final_ext = f.split('.')[-1]
                        break
                
                if found_file:
                    st.success("✅ Download Complete!")
                    with open(found_file, "rb") as file:
                        st.download_button(
                            label=f"📥 Save .{final_ext}",
                            data=file,
                            file_name=f"video.{final_ext}",
                            mime="application/octet-stream"
                        )
                else:
                    st.error("Error: File not found after download.")

            except Exception as e:
                st.error(f"Download Error: {e}")