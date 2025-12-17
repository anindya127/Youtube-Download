import streamlit as st
import yt_dlp
import os
import pandas as pd

# 1. Setup Directories & Config
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

st.title("🎥 YouTube Downloader (Anti-Block)")

url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("Analyze Video"):
        with st.spinner("Fetching video details..."):
            try:
                # Configure options just to fetch metadata
                ydl_opts = {
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web_embedded']
                        }
                    },
                    'nocheckcertificate': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.success(f"Found: {info.get('title')}")

            except Exception as e:
                st.error(f"Error fetching info: {e}")

# 3. Display Options & Download
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    st.write(f"**Video:** {info.get('title')}")
    
    option = st.selectbox(
        "Choose Format:",
        ("Best Video (Merged)", "Audio Only (MP3)")
    )

    if st.button("Download Now"):
        with st.spinner("Downloading..."):
            try:
                # Clean up old files in downloads to save space
                for f in os.listdir(DOWNLOAD_FOLDER):
                    os.remove(os.path.join(DOWNLOAD_FOLDER, f))

                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"

                ydl_opts = {
                    'outtmpl': output_path,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web_embedded']
                        }
                    }
                }
                
                if "Audio" in option:
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                    final_ext = "mp3"
                else:
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                    final_ext = "mp4"

                # Run Download
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Find the resulting file
                downloaded_file = None
                for f in os.listdir(DOWNLOAD_FOLDER):
                    if f.startswith(safe_filename):
                        downloaded_file = os.path.join(DOWNLOAD_FOLDER, f)
                        final_real_ext = f.split('.')[-1]
                        break

                if downloaded_file:
                    st.success("Processing Complete!")
                    with open(downloaded_file, "rb") as file:
                        st.download_button(
                            label=f"Save {final_real_ext.upper()} to Device",
                            data=file,
                            file_name=f"{info['title']}.{final_real_ext}",
                            mime="application/octet-stream"
                        )
            except Exception as e:
                st.error(f"Download failed: {e}")