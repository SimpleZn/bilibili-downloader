# Bilibili Video Downloader

**Features**:
- Supports both BVids and direct URLs
- Multiple output formats (MP4/FLV/MP3)
- Quality selection (480p-1080p)
- Cookie authentication for private content
- Automatic temp file cleanup

A Python tool to download videos and audio from Bilibili with metadata preservation and format conversion.

## Features
- Download high-quality videos with audio
- Extract and preserve video metadata
- Convert audio to MP3 format
- Handle age-restricted/content-protected videos
- Progress tracking with resumable downloads
- Automatic directory organization

## Prerequisites
- Python 3.6+
- FFmpeg (must be installed and added to system PATH)

## Installation
```bash
pip install -r requirements.txt
```

## Cookie Setup (For Private/Protected Content)
1. Login to Bilibili in your browser
2. Use developer tools (F12) to copy the `SESSDATA` cookie value
3. Use cookie with:
```bash
python src/bilibili_downloader.py BV1xx411c7mh --sessdata YOUR_SESSDATA
```

## Installation & Usage

**Install requirements:**
```bash
pip install -r requirements.txt
```

**Basic commands:**
```bash
# Using BVid or URL
python src/bilibili_downloader.py BV1xx411c7mh
python src/bilibili_downloader.py 'https://www.bilibili.com/video/BV1xx411c7mh'

# Quality selection (80=1080p, 64=720p, 32=480p)
python src/bilibili_downloader.py BV1xx411c7mh -q 64

# Format options (mp4/flv/mp3)
python src/bilibili_downloader.py BV1xx411c7mh -f flv
```

## Output Structure
```
output/
└── Video_Title_Shortened/
    ├── Video_Title_Shortened.mp4
    ├── Video_Title_Shortened.mp3
    └── temp/ (auto-cleaned)
```

## Error Handling
Common errors and solutions:

| Error Code | Description | Solution |
|------------|-------------|----------|
| -101 | Invalid cookie | Renew SESSDATA cookie |
| -404 | Video not found | Verify BVid/URL format |
| 62002 | Geo-restricted | Use VPN/cookie |
| -400 | Invalid URL/BVid | Use format: BV... or https://... |
| -501 | FFmpeg missing | Install ffmpeg and add to PATH |

## Security Considerations
⚠️ **Important**:
- SESSDATA cookies are **login credentials** - treat as passwords
- Recommended cookie usage:
  ```bash
  # Use environment variable instead of CLI argument
  export SESSDATA='your_cookie' && python src/bilibili_downloader.py BV...
  ```
- Automatically excluded from git via .gitignore
- Session cookies expire after 30 days

## License
MIT License