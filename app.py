import streamlit as st
import yt_dlp
import os
import pandas as pd

# 1. Setup Directories & Config
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Check for cookies.txt in the repository
COOKIE_FILE = "cookies.txt"
use_cookies = os.path.exists(COOKIE_FILE)

st.set_page_config(page_title="Pro YouTube Downloader", page_icon="📺")
st.title("Pro YouTube Downloader")

if use_cookies:
    st.success("'cookies.txt' found! Premium formats (1080p Premium/Age-gated) unlocked.")
else:
    st.warning("'cookies.txt' not found. Some videos or high qualities might be blocked.")

# 2. Input URL
url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("Analyze Video"):
        with st.spinner("Fetching video details..."):
            try:
                # Configure options just to fetch metadata
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_FILE

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.success(f"Found: {info.get('title')}")

            except Exception as e:
                st.error(f"Error fetching info: {e}")

# 3. Display Options & Download
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    st.image(info.get('thumbnail'), width=300)
    st.write(f"**Title:** {info.get('title')}")
    
    # --- PREPARE DATA FOR TABLE ---
    formats = info.get('formats', [])
    video_options = []
    
    # Filter formats to show only useful ones (Video with or without audio)
    for f in formats:
        # We only want formats that have video (vcodec != none)
        if f.get('vcodec') != 'none':
            f_id = f.get('format_id')
            ext = f.get('ext')
            res = f.get('resolution')
            note = f.get('format_note', '')
            fps = f.get('fps')
            filesize = f.get('filesize_approx') or f.get('filesize')
            
            # Convert filesize to MB if available
            size_mb = f"{filesize / 1024 / 1024:.1f} MB" if filesize else "N/A"
            
            # Create a label for the dropdown
            label = f"ID: {f_id} | {res} | {ext} | {fps}fps | {note} | Size: {size_mb}"
            video_options.append((label, f_id))

    # --- SHOW TABLE (Visual Only) ---
    st.write("### Available Resolutions")
    
    # Create a clean dataframe for the user to look at
    table_data = []
    for label, f_id in video_options:
        parts = label.split('|')
        table_data.append({
            "Format ID": parts[0].replace("ID: ", "").strip(),
            "Resolution": parts[1].strip(),
            "Ext": parts[2].strip(),
            "FPS": parts[3].strip(),
            "Note": parts[4].strip(),
            "Size": parts[5].strip()
        })
    
    if table_data:
        df = pd.DataFrame(table_data)
        # Sort by resolution (roughly) or ID to put best on top is tricky, 
        # so we just display what yt-dlp gave us (usually low to high)
        st.dataframe(df, use_container_width=True)

    # --- SELECTION MENU ---
    st.write("### Download Options")
    download_type = st.radio("Select Type:", ["Video", "Audio Only (MP3)"])

    selected_format_id = None
    
    if download_type == "Video":
        # Reverse list so highest quality is usually at the bottom/top depending on list
        # We let user pick from the string list
        selected_label = st.selectbox(
            "Select Video Quality (Matches Table Above):", 
            [opt[0] for opt in reversed(video_options)]
        )
        # Find the ID associated with the label
        for label, f_id in video_options:
            if label == selected_label:
                selected_format_id = f_id
                break

    # 4. Download Button
    if st.button("Download Selected Format"):
        with st.spinner("Processing on server... (This may take time for 4K)"):
            try:
                # Clean up old files in downloads to save space
                for f in os.listdir(DOWNLOAD_FOLDER):
                    os.remove(os.path.join(DOWNLOAD_FOLDER, f))

                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"
                
                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_FILE

                final_ext = "mp4" # default guess

                if download_type == "Audio Only (MP3)":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                    final_ext = "mp3"
                
                else:
                    # VIDEO MODE:
                    # We download the User Selected Video + The Best Audio
                    # This ensures sound works even if they pick a "video only" 4K stream
                    ydl_opts['format'] = f"{selected_format_id}+bestaudio/best"
                    ydl_opts['merge_output_format'] = 'mp4' # Force merge into MP4
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
                else:
                    st.error("File processing failed. Please try a lower resolution.")

            except Exception as e:
                st.error(f"Error: {e}")