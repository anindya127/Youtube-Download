import streamlit as st
import yt_dlp
import os
import pandas as pd

# 1. Setup
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

st.set_page_config(page_title="YouTube Format Analyzer", page_icon="🔬", layout="wide")
st.title("🔬 YouTube Video Analyzer & Downloader")

# 2. Cookies (Optional but Recommended)
COOKIE_FILE = "cookies.txt"
if os.path.exists(COOKIE_FILE):
    COOKIE_PATH = os.path.abspath(COOKIE_FILE)
    use_cookies = True
    st.success("✅ Cookies found! (Premium/Age-gated content unlocked)")
else:
    COOKIE_PATH = None
    use_cookies = False
    st.info("ℹ️ No cookies found. (Standard access only)")

# 3. URL Input
url = st.text_input("Paste YouTube URL here:")

if url:
    if st.button("🔍 Analyze Formats"):
        with st.spinner("Fetching full format list..."):
            try:
                # We use specific client args to ensure we see Web (4K) and Android (1080p)
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
                    st.toast("Analysis Complete!", icon="✅")

            except Exception as e:
                st.error(f"Analysis failed: {e}")

# 4. Display Results
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    
    # Metadata
    col1, col2 = st.columns([1, 3])
    with col1:
        if info.get('thumbnail'):
            st.image(info.get('thumbnail'), width="stretch")
    with col2:
        st.subheader(info.get('title'))
        st.write(f"**Channel:** {info.get('uploader')}")
        st.write(f"**Duration:** {info.get('duration_string')}")

    # --- BUILD THE TABLE ---
    formats = info.get('formats', [])
    data_list = []
    
    for f in formats:
        # We only care about VIDEO or AUDIO (ignore none/none)
        if f.get('vcodec') == 'none' and f.get('acodec') == 'none':
            continue

        f_id = f.get('format_id')
        ext = f.get('ext')
        filesize = f.get('filesize') or f.get('filesize_approx')
        
        # Human readable size
        if filesize:
            size_str = f"{filesize / 1024 / 1024:.1f} MB"
        else:
            size_str = "Unknown"

        # Video details
        if f.get('vcodec') != 'none':
            res = f"{f.get('height')}p"
            fps = f"{f.get('fps')}fps"
            codec = f.get('vcodec')
            type_label = "Video"
            # Check if it has audio
            has_audio = "Yes" if f.get('acodec') != 'none' else "No (Video Only)"
        else:
            res = "Audio Only"
            fps = "-"
            codec = f.get('acodec')
            type_label = "Audio"
            has_audio = "Yes"

        # Add to list
        data_list.append({
            "ID": f_id,
            "Type": type_label,
            "Resolution": res,
            "FPS": fps,
            "Ext": ext,
            "Size": size_str,
            "Codec": codec,
            "Audio?": has_audio,
            # Hidden sort key (Height)
            "_sort": f.get('height') or 0
        })

    # Create DataFrame
    df = pd.DataFrame(data_list)
    # Sort by Resolution (High to Low)
    df = df.sort_values(by="_sort", ascending=False)

    # Show the table to the user
    st.write("### 📊 All Available Formats")
    st.dataframe(
        df[["ID", "Type", "Resolution", "FPS", "Ext", "Size", "Audio?", "Codec"]], 
        hide_index=True, 
        width="stretch"
    )

    # --- DOWNLOAD SECTION ---
    st.write("### ⬇️ Select & Download")
    
    # Create a list of options for the dropdown
    # Format: "ID: 137 | 1080p | 30fps | mp4 | Video Only"
    dropdown_options = []
    for index, row in df.iterrows():
        label = f"ID: {row['ID']} | {row['Resolution']} | {row['FPS']} | {row['Ext']} | {row['Audio?']}"
        dropdown_options.append((label, row['ID'], row['Type'], row['Audio?']))

    selected_tuple = st.selectbox("Pick a format from the list:", dropdown_options, format_func=lambda x: x[0])
    
    if st.button("🚀 Download Selected Format"):
        target_id = selected_tuple[1]
        target_type = selected_tuple[2]
        has_audio = selected_tuple[3]
        
        with st.spinner(f"Downloading Format ID: {target_id}..."):
            try:
                # Cleanup
                for f in os.listdir(DOWNLOAD_FOLDER):
                    os.remove(os.path.join(DOWNLOAD_FOLDER, f))
                
                safe_filename = "download"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"

                ydl_opts = {
                    'outtmpl': output_path,
                    'restrictfilenames': True,
                    'extractor_args': {'youtube': {'player_client': ['web', 'android']}},
                    # Important: Don't force format merge if not needed
                }
                if use_cookies:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                # --- SMART LOGIC ---
                if target_type == "Audio":
                    # Download audio and convert to MP3
                    ydl_opts['format'] = target_id
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }]
                
                elif "No" in has_audio:
                    # Video Only selected -> Must merge with best audio
                    st.info("ℹ️ You selected a 'Video Only' stream. Merging with best available audio...")
                    ydl_opts['format'] = f"{target_id}+bestaudio"
                    ydl_opts['merge_output_format'] = 'mkv' # Safe container for high res
                
                else:
                    # Video has audio -> Download exactly as is
                    ydl_opts['format'] = target_id

                # Run Download
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Serve File
                downloaded_file = None
                for f in os.listdir(DOWNLOAD_FOLDER):
                    if f.startswith(safe_filename):
                        downloaded_file = os.path.join(DOWNLOAD_FOLDER, f)
                        final_ext = f.split('.')[-1]
                        break
                
                if downloaded_file:
                    st.success("✅ Download Complete!")
                    with open(downloaded_file, "rb") as file:
                        st.download_button(
                            label=f"📥 Save File (. {final_ext})",
                            data=file,
                            file_name=f"{info['title']}.{final_ext}",
                            mime="application/octet-stream"
                        )
                else:
                    st.error("Download finished but file not found.")

            except Exception as e:
                st.error(f"Error: {e}")