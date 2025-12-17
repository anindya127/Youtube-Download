# Pro YouTube Downloader 📺

A professional YouTube video and audio downloader with both web interface and command-line support.

## 🌐 Live Web App

**Try it now:** [https://youtube-download-web-m4fey9zujtwtaqbf8txpfj.streamlit.app/](https://youtube-download-web-m4fey9zujtwtaqbf8txpfj.streamlit.app/)

## Features

### Web Interface (app.py)

- **User-friendly Streamlit interface** - No coding required
- **Smart format selection** - View all available resolutions in a clean table
- **Video downloads** - Choose from multiple quality options (360p to 4K)
- **Audio extraction** - Download and convert to MP3
- **Premium support** - Unlocks age-gated and premium formats with cookies.txt
- **Real-time preview** - See video thumbnail and details before downloading
- **Direct download** - Get files instantly through your browser

### Command-Line Tool (main.py)

- **Advanced options** - More control over download settings
- **4K/8K support** - Handle ultra-high-resolution videos
- **Format selection** - Choose specific format IDs
- **Batch processing** - Can be automated with scripts
- **Optimal for large files** - Better for downloading very high-resolution content

## 🚀 Quick Start

### Using the Web App

1. Visit [https://youtube-download-web-m4fey9zujtwtaqbf8txpfj.streamlit.app/](https://youtube-download-web-m4fey9zujtwtaqbf8txpfj.streamlit.app/)
2. Paste any YouTube URL
3. Click "Analyze Video"
4. Select your preferred quality from the table
5. Click "Download Selected Format"
6. Save the file to your device

### Using the Command-Line Tool (For 4K/8K Videos)

If you need to download **4K or 8K resolution videos**, use the command-line version:

#### Prerequisites

1. **Python 3.7+** installed on your system
2. **FFmpeg** - Download from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
   - Extract the downloaded archive
   - Add the `bin` folder to your system PATH, or place `ffmpeg.exe` in the same folder as main.py

#### Installation

```bash
# Clone or download this repository
git clone https://github.com/anindya127/Youtube-Download.git
cd Youtube-Download

# Install required packages
pip install -r requirements.txt
```

#### Usage

```bash
# Interactive mode
python main.py

# Direct URL mode
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Options:**

1. **Best Quality Video** - Automatically merges best video + audio
2. **Audio Only (MP3)** - Extract and convert to MP3 format
3. **Custom Format** - Enter specific format ID for precise control

## 📋 Requirements

- Python 3.7+
- yt-dlp
- streamlit (for web app)
- pandas (for web app)
- FFmpeg (for merging video/audio and conversion)

## 🎯 Why Use main.py for 4K/8K?

The command-line version (main.py) with local FFmpeg is recommended for ultra-high-resolution downloads because:

- Better handling of large file sizes
- More reliable merging of video and audio streams
- Faster processing on your local machine
- No server limitations or timeouts

## 🍪 Premium Features (Optional)

To access age-restricted or premium content:

1. Export your YouTube cookies using a browser extension
2. Save as `cookies.txt` in the project folder
3. The app will automatically detect and use them

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for personal use only. Please respect copyright laws and YouTube's Terms of Service. Only download content you have the right to download.

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements!

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using Python, yt-dlp, and Streamlit**
