import streamlit as st
import yt_dlp
import os
import pandas as pd
import shutil

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Check for cookies (Crucial for 4K on Cloud)
COOKIE_FILE = "cookies.txt"
if os.path.exists(COOKIE_FILE):
    COOKIE_PATH = os.path.abspath(COOKIE_FILE)
    use_cookies = True
else:
    COOKIE_PATH = None
    use_cookies = False

st.set_page_config(page_title="Direct YouTube Downloader", page_icon="⬇️", layout="wide")
st.title("⬇️ Direct YouTube Downloader (Manual Selection)")

# --- STATUS CHECK ---
# Shows if the server is ready for high quality
col1, col2 = st.columns(2)
with col1:
    if shutil.which("ffmpeg"):
        st.success("✅ FFmpeg Active")
    else:
        st.error("❌ FFmpeg Missing (Merge will fail)")
with col2:
    if use_cookies:
        st.success("✅ Cookies Active (4K Unlocked)")
    else:
        st.warning("⚠️ No Cookies (4K might fail)")

# --- STEP 1: INPUT ---
url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("🔍 1. Fetch Formats"):
        with st.spinner("Fetching format list..."):
            try:
                # We use 'web' client to see 4K, just like your local script
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {'youtube': {'player_client': ['web', 'android']}},
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.toast("Formats Loaded!", icon="✅")

            except Exception as e:
                st.error(f"Error: {e}")

# --- STEP 2: DISPLAY TABLE ---
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    
    st.write(f"**Video Title:** {info.get('title')}")
    
    # Process formats exactly like your local script
    formats = info.get('formats', [])
    data_list = []
    
    for f in formats:
        # Filter (Show Video+Audio or Audio-only)
        if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
            f_id = f.get('format_id')
            ext = f.get('ext')
            res = f.get('resolution') if f.get('resolution') else "Audio Only"
            note = f.get('format_note') if f.get('format_note') else ""
            
            # Create a label for the dropdown
            label = f"ID: {f_id} | {ext} | {res} | {note}"
            
            data_list.append({
                "Label": label,
                "ID": f_id,
                "Resolution": res,
                "Ext": ext,
                "Note": note
            })
    
    # Show the table (Reversed so high quality is top)
    if data_list:
        df = pd.DataFrame(data_list)
        st.dataframe(df[["ID", "Ext", "Resolution", "Note"]], hide_index=True, width=800)
    
    # --- STEP 3: MANUAL SELECTION ---
    st.write("### ⬇️ Select Options")
    
    # Option 1: Pick from list
    selected_row = st.selectbox(
        "Choose a Format ID:",
        reversed(data_list), # Best quality usually at bottom of list, so we reverse it
        format_func=lambda x: x['Label']
    )
    
    # Option 2: Choose Mode (like your local script's Option 1/2/3)
    mode = st.radio("Download Mode:", ["Video (Merge with Audio)", "Audio Only (MP3)"])

    if st.button("🚀 Download Now"):
        target_id = selected_row['ID']
        
        with st.spinner("Downloading..."):
            try:
                # Clean old files
                if os.path.exists(DOWNLOAD_FOLDER):
                    shutil.rmtree(DOWNLOAD_FOLDER)
                os.makedirs(DOWNLOAD_FOLDER)

                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"
                
                # BASE OPTIONS
                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    'extractor_args': {'youtube': {'player_client': ['web', 'android']}},
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                # LOGIC FROM YOUR LOCAL SCRIPT
                if mode == "Audio Only (MP3)":
                    # Option 2 in local script
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                else:
                    # Option 3 in local script (Specific ID + Best Audio)
                    # We force MKV container because 4K WebM + Audio often fails in MP4 on Cloud
                    ydl_opts['format'] = f"{target_id}+bestaudio/best"
                    ydl_opts['merge_output_format'] = 'mkv' 

                # RUN DOWNLOAD
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # SERVE FILE
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
                            file_name=f"{info['title']}.{final_ext}",
                            mime="application/octet-stream"
                        )
                else:
                    st.error("Download finished, but file was not found.")

            except Exception as e:
                st.error(f"Download Error: {e}")