import streamlit as st
import yt_dlp
import os
import shutil

# --- SETUP ---
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Check for cookies
COOKIE_FILE = "cookies.txt"
if os.path.exists(COOKIE_FILE):
    COOKIE_PATH = os.path.abspath(COOKIE_FILE)
    use_cookies = True
else:
    COOKIE_PATH = None
    use_cookies = False

st.set_page_config(page_title="Brute Force Downloader", layout="wide")
st.title("🛡️ YouTube Downloader (Brute Force Mode)")

# --- 1. SETTINGS ---
st.write("### ⚙️ Configuration")
col1, col2 = st.columns(2)
with col1:
    # CLIENT SWITCHER: This is the fix for "Format not available"
    # If one fails, the user can try another.
    client = st.selectbox(
        "YouTube Client (Change this if download fails):",
        ["web (Best for 4K)", "ios (Good Alternate)", "android (Safe/1080p)", "tv_embedded (Legacy)"]
    )
with col2:
    # COOKIE TOGGLE: Sometimes cookies from a different IP cause the crash
    enable_cookies = st.checkbox("Use cookies.txt?", value=use_cookies, disabled=not use_cookies)

# --- 2. INPUT ---
url = st.text_input("Paste YouTube URL:")

# --- 3. ANALYZE (Simple Version) ---
if url:
    if st.button("🔍 Find Formats"):
        with st.spinner("Scanning..."):
            try:
                # We analyze using the SELECTED client
                ydl_opts = {
                    'quiet': True,
                    'extractor_args': {'youtube': {'player_client': [client]}},
                }
                if enable_cookies and COOKIE_PATH:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.session_state['current_client'] = client # Remember which client found these
                    st.success(f"Found: {info.get('title')}")

            except Exception as e:
                st.error(f"Analysis failed using '{client}' client. Try switching to 'android' or 'ios'.")
                st.error(e)

# --- 4. DOWNLOAD ---
if 'video_info' in st.session_state:
    info = st.session_state['video_info']
    
    st.write(f"**Target:** {info['title']}")
    
    # Simple list of formats
    formats = info.get('formats', [])
    options = []
    for f in formats:
        if f.get('vcodec') != 'none':
            label = f"ID: {f['format_id']} | {f.get('resolution', '???')} | {f.get('ext')} | {f.get('note', '')}"
            options.append((label, f['format_id']))
    
    # Reverse so high quality is top
    options.reverse()
    
    selected_option = st.selectbox("Select Format:", options, format_func=lambda x: x[0])
    
    if st.button("🚀 Force Download"):
        target_id = selected_option[1]
        active_client = st.session_state.get('current_client', 'web')
        
        with st.spinner(f"Attempting download using '{active_client}' client..."):
            try:
                # CLEANUP
                if os.path.exists(DOWNLOAD_FOLDER):
                    shutil.rmtree(DOWNLOAD_FOLDER)
                os.makedirs(DOWNLOAD_FOLDER)
                
                safe_filename = "video"
                output_path = f"{DOWNLOAD_FOLDER}/{safe_filename}.%(ext)s"

                # --- METHOD 1: PRECISE ID ---
                # We try to download EXACTLY what you asked for
                ydl_opts = {
                    'outtmpl': output_path,
                    'extractor_args': {'youtube': {'player_client': [active_client]}},
                    # We force MKV to avoid container errors
                    'merge_output_format': 'mkv', 
                }
                
                if enable_cookies and COOKIE_PATH:
                    ydl_opts['cookiefile'] = COOKIE_PATH

                # LOGIC:
                # 1. Try Specific ID + Best Audio
                # 2. If that crashes, Fallback to "Best Video" generic command
                try:
                    ydl_opts['format'] = f"{target_id}+bestaudio/best"
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception as e:
                    st.warning(f"Precise download failed ({e}). Trying fallback...")
                    
                    # FALLBACK: Just get best quality availble
                    ydl_opts['format'] = "bestvideo+bestaudio/best"
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                # --- SERVE FILE ---
                found = False
                for f in os.listdir(DOWNLOAD_FOLDER):
                    if f.startswith(safe_filename):
                        filepath = os.path.join(DOWNLOAD_FOLDER, f)
                        with open(filepath, "rb") as file:
                            st.download_button(
                                label="📥 Save Video",
                                data=file,
                                file_name=f"download.{f.split('.')[-1]}",
                                mime="application/octet-stream"
                            )
                        found = True
                        break
                
                if not found:
                    st.error("Download finished but file missing. YouTube likely blocked the stream.")

            except Exception as e:
                st.error(f"Critical Failure: {e}")