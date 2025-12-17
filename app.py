import streamlit as st
import yt_dlp
import os

# Set the download directory
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

st.title("🎥 My Web YouTube Downloader")

url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("Check Resolutions"):
        with st.spinner("Fetching info..."):
            try:
                ydl_opts = {}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.success(f"Found: {info['title']}")
            except Exception as e:
                st.error(f"Error: {e}")

if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    st.write(f"**Title:** {info['title']}")
    
    option = st.selectbox(
        "Choose Format:",
        ("Best Video + Audio (Merged)", "Audio Only (MP3)")
    )

    if st.button("Download Now"):
        with st.spinner("Downloading..."):
            try:
                ydl_opts = {
                    'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
                }
                
                if option == "Audio Only (MP3)":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                else:
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                st.success("Download Complete! Check the 'downloads' folder on the server.")
                
                # Note: In a real web app, you would add code here to 
                # send the file from the server to the user's browser.
                
            except Exception as e:
                st.error(f"Error: {e}")