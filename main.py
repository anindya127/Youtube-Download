import yt_dlp
import sys


def list_resolutions(url):
    """
    Fetches and displays available video resolutions and audio options.
    """
    print("\nFetching video information... Please wait.")

    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            print(f"\nTitle: {info.get('title')}")
            print("-" * 50)
            print(f"{'ID':<10} | {'Format':<10} | {'Resolution':<15} | {'Note'}")
            print("-" * 50)

            # Filter and display relevant formats
            for f in formats:
                # We show video formats (mp4/webm) and audio only
                if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                    f_id = f.get('format_id')
                    ext = f.get('ext')
                    res = f.get('resolution') if f.get(
                        'resolution') else "Audio Only"
                    note = f.get('format_note') if f.get('format_note') else ""

                    # Clean up the output to make it readable
                    if res == "Audio Only":
                        print(f"{f_id:<10} | {ext:<10} | {res:<15} | {note}")
                    elif f.get('vcodec') != 'none':
                        print(f"{f_id:<10} | {ext:<10} | {res:<15} | {note}")

        except Exception as e:
            print(f"Error fetching info: {e}")
            return None
    return info


def download_video(url):
    print("\n--- YouTube Downloader & Converter ---")

    # Step 1: List Formats
    info = list_resolutions(url)
    if not info:
        return

    print("-" * 50)
    print("OPTIONS:")
    print("1. Download Best Quality Video (Auto-merge Video+Audio)")
    print("2. Download Audio Only (Convert to MP3)")
    print("3. Enter a specific Format ID from the list above")

    choice = input("\nEnter your choice (1/2/3): ").strip()

    ydl_opts = {}

    if choice == '1':
        # Downloads the best video and best audio and merges them
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
        }
    elif choice == '2':
        # Downloads audio and converts to mp3
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
        }
    elif choice == '3':
        f_id = input("Enter the Format ID (e.g., 137, 22, 140): ")
        # If user picks a video-only stream, we try to merge best audio to it
        ydl_opts = {
            'format': f'{f_id}+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
        }
    else:
        print("Invalid choice.")
        return

    # Step 2: Download
    print("\nStarting Download...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\nDownload & Conversion Complete!")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        video_url = input("Enter YouTube URL: ")

    download_video(video_url)
