# Bilibili Video Downloader GUI

A simple GUI application for downloading videos and their audio tracks from Bilibili.com.

## Features

- Download Bilibili videos by URL or BVID.
- Saves both a video file (e.g., MP4) and a separate MP3 audio file.
- GUI for settings:
    - SESSDATA cookie for accessing HD formats and login-required content.
    - Video quality selection.
    - Video output format (e.g., mp4, mkv - defaults to mp4 if an audio format like mp3 is entered).
    - Custom path to FFmpeg executable.
    - Custom download directory (defaults to your system's Downloads folder, organizing files into `Bilibili_Downloads/VideoTitle/`).
- Progress bar and status messages during download.
- Ability to stop ongoing downloads.

## Prerequisites

1.  **Python 3**: Ensure you have Python 3 installed. (Tested with Python 3.12+)
2.  **FFmpeg**: This application requires FFmpeg for merging video/audio streams and converting audio to MP3.
    -   **macOS (with Homebrew)**: `brew install ffmpeg`
    -   **Other OS**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and ensure it's in your system's PATH or provide the full path in the application settings.

## Setup and Installation

1.  **Clone the Repository (if applicable) or Download Files**:
    ```bash
    # If you have it as a git repo
    # git clone <repository_url>
    # cd <repository_directory>
    ```

2.  **Create a Virtual Environment (Recommended)**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    Make sure you have a `requirements.txt` file with the following content:
    ```txt
    PyQt5
    py2app
    requests
    tqdm
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

### Option 1: Directly from Python (for development/testing)

```bash
python3 src/main_app.py
```

### Option 2: Building a macOS App Bundle

1.  **Create an Icon (Optional but Recommended)**:
    -   Create an icon file named `icon.icns` in the root directory of the project. You can use online converters to create an `.icns` file from a PNG.

2.  **Build the App**:
    The `setup.py` file is configured to use `py2app`.
    ```bash
    python3 setup.py py2app -A  # Alias mode for faster development builds
    # For a distributable app, you might use:
    # python3 setup.py py2app
    ```

3.  **Run the App**:
    The application bundle (`Bilibili Downloader.app`) will be created in the `dist` directory. Double-click it to run.

## First Time Use & Settings

1.  **Authorization (SESSDATA)**:
    -   On first launch (or if `SESSDATA` is not configured), an authorization window will appear.
    -   Click "Open Bilibili Login" to go to the Bilibili login page in your browser.
    -   After logging in, you need to retrieve the `SESSDATA` cookie:
        1.  In your browser (e.g., Chrome, Firefox), open Developer Tools (usually by right-clicking on the page and selecting "Inspect" or pressing F12).
        2.  Go to the "Application" (Chrome) or "Storage" (Firefox) tab.
        3.  Under "Cookies", find `https://www.bilibili.com`.
        4.  Locate the cookie named `SESSDATA` and copy its "Value".
    -   Paste this value into the SESSDATA input field in the app and click "Submit SESSDATA".

2.  **Settings Page**:
    -   After authorization, or on subsequent launches, the main settings page will appear.
    -   **SESSDATA**: Your Bilibili SESSDATA cookie.
    -   **Quality**: Video quality setting (e.g., 80 for 1080p, 116 for 4K - consult Bilibili standards if needed).
    -   **Format**: Desired *video* output format. Common choices include `mp4`, `mkv`, `mov`, `avi`, `flv`, `webm`. An MP3 audio file will always be generated separately. If you enter an audio-only format like `mp3` here, the video will default to `mp4`.
    -   **FFmpeg Path**: Full path to the `ffmpeg` executable. If `ffmpeg` is in your system PATH, you can leave this as `ffmpeg`. Use "Browse" to locate it if needed.
    -   **Download Path**: Directory where downloaded files will be saved. Defaults to your system's "Downloads" folder. Files will be organized into `[Selected Path]/Bilibili_Downloads/[Video Title]/`.
    -   Click "Save Settings" to save your preferences. These are stored in `~/.bilibili_downloader_config.json`.

3.  **Resetting Settings**:
    -   If you need to reset all application settings to their defaults, you can do so by deleting the configuration file.
    -   Close the Bilibili Downloader application.
    -   Open your Terminal and run the following command:
        ```bash
        rm -f ~/.bilibili_downloader_config.json
        ```
    -   The next time you start the application, it will be as if it's the first launch, and a new default configuration file will be created when you save settings.

## Downloading Videos

1.  Enter the Bilibili video URL (e.g., `https://www.bilibili.com/video/BVxxxxxxxxxx`) or just the BVID (e.g., `BVxxxxxxxxxx`) into the "Bilibili Video URL or BVID" field.
2.  Ensure your settings (quality, format, paths) are configured as desired.
3.  Click "Download Video".
4.  The progress bar and status area will show the download progress.
5.  You can click "Stop Download" to cancel an ongoing download.
6.  Completed files (video and MP3 audio) will be in your specified download path, under `Bilibili_Downloads/[Video Title]/`.

## Notes

- The `output` folder in the project root is used as a fallback if the download path setting is not configured or accessible (primarily for CLI script usage).
- The application creates a `temp` subfolder within each video's download directory for temporary files, which are cleaned up after the download (or on error/stop).

## License
MIT License