import streamlit as st
import yt_dlp
import os

# Create downloads directory
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

st.title("🎥 YouTube Downloader (Anti-Block)")

url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("Check Resolutions"):
        with st.spinner("Attempting to bypass YouTube blocks..."):
            try:
                # TRICK: We tell YouTube we are an Android device, not a server
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
                    st.success(f"Success! Found: {info.get('title', 'Unknown Title')}")
            
            except Exception as e:
                st.error("YouTube blocked the connection.")
                st.error(f"Technical Error: {e}")

# Only show options if we successfully got the info
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
                # Use a safe filename
                safe_filename = "downloaded_video"
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

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Find the file to provide download button
                downloaded_file = None
                for f in os.listdir(DOWNLOAD_FOLDER):
                    if f.startswith(safe_filename):
                        downloaded_file = os.path.join(DOWNLOAD_FOLDER, f)
                        break
                
                if downloaded_file:
                    with open(downloaded_file, "rb") as file:
                        st.download_button(
                            label="📥 Save to Device",
                            data=file,
                            file_name=f"video.{final_ext}",
                            mime="application/octet-stream"
                        )
            except Exception as e:
                st.error(f"Download failed: {e}")