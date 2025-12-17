import streamlit as st
import yt_dlp
import os

# Create downloads directory
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

st.title("🎥 YouTube Downloader (With Cookies)")
st.write("To bypass the '403 Forbidden' error, upload your cookies.txt file.")

# 1. Input Section
url = st.text_input("Paste YouTube URL here:")
cookie_file = st.file_uploader("Upload cookies.txt (Required for Web Servers)", type=["txt"])

if url and cookie_file:
    # Save the uploaded cookie file temporarily
    with open("cookies.txt", "wb") as f:
        f.write(cookie_file.getbuffer())
    
    if st.button("Check Video"):
        with st.spinner("Authenticating and fetching info..."):
            try:
                ydl_opts = {
                    'cookiefile': 'cookies.txt', # <--- THIS IS THE KEY FIX
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.success(f"Success! Found: {info.get('title')}")
            except Exception as e:
                st.error(f"Error: {e}")

# 2. Download Section
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    st.write(f"**Title:** {info['title']}")
    
    option = st.selectbox(
        "Choose Format:",
        ("Best Video (Merged)", "Audio Only (MP3)")
    )

    if st.button("Download Now"):
        with st.spinner("Downloading..."):
            try:
                safe_filename = "downloaded_video"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"
                
                ydl_opts = {
                    'cookiefile': 'cookies.txt', # Pass cookies to download too
                    'outtmpl': output_path,
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

                # Find the file
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