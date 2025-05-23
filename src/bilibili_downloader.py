import requests
import argparse
import json
import subprocess
import os
import re
from tqdm import tqdm
import urllib.parse
import threading

FFMPEG_PATH = "ffmpeg" # Default command
# Default base path for downloads if not specified by GUI/caller
# For CLI, this will be relative to where the script is run ('output')
# For GUI, the main_app.py will pass a full path from settings.
DEFAULT_OUTPUT_BASE_PATH = "output" 

class BilibiliDownloader:
    @staticmethod
    def sanitize_folder_name(name):
        # Remove special characters and replace spaces
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized[:50]  # Limit folder name length

    def __init__(self, sessdata=None):
        if sessdata:
            sessdata = urllib.parse.unquote(sessdata)
        self.cookies = {'SESSDATA': sessdata} if sessdata else {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/'
        }

    def get_video_info(self, bvid):
        if not self.cookies.get('SESSDATA') and not bvid.startswith('BV'):
            raise ValueError("Invalid BVid format. Example: BV1xx411c7mh")
            
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        response = requests.get(url, headers=self.headers, cookies=self.cookies)
        
        try:
            data = response.json()
            if data.get('code') == -101:
                raise Exception("Invalid/expired SESSDATA cookie - get fresh cookie from logged-in browser")
            if not data.get('data'):
                raise Exception(f"API response error: {data.get('message')} (Code {data['code']})")
        except json.JSONDecodeError:
            raise Exception(f"Invalid API response: {response.text[:200]}")

        if data['code'] != 0:
            if data['code'] == -404:
                raise Exception("Video not found or requires login - use valid SESSDATA cookie")
            raise Exception(f"Bilibili API error ({data['code']}): {data.get('message')}")

        return {
            'title': data['data']['title'],
            'pages': data['data']['pages'],
            'cid': data['data']['cid'],
            'quality': data['data'].get('accept_quality', [])
        }

    def download_video(self, bvid, quality=80, output_format='mp4', progress_callback=None, stop_event=None, ffmpeg_path=None, custom_output_base_path=None):
        global FFMPEG_PATH
        if ffmpeg_path:
            FFMPEG_PATH = ffmpeg_path
        else:
            ffmpeg_path = FFMPEG_PATH 

        video_info = self.get_video_info(bvid)
        
        if progress_callback:
            progress_callback(0, 100, f"Fetching video info for: {video_info['title']}")

        sanitized_title = self.sanitize_folder_name(video_info['title'])
        
        # Determine the base output directory
        if custom_output_base_path:
            # Create a specific subfolder within the custom path for our downloads
            # e.g., /Users/user/Downloads/Bilibili_Downloads/VideoTitle
            base_download_dir = os.path.join(custom_output_base_path, "Bilibili_Downloads")
        else:
            # Fallback for CLI or if no path is given from GUI
            base_download_dir = DEFAULT_OUTPUT_BASE_PATH
            
        output_dir = os.path.join(base_download_dir, sanitized_title)
        os.makedirs(output_dir, exist_ok=True) # Ensure base_download_dir and output_dir are created
        
        temp_dir = os.path.join(output_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        play_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={video_info['cid']}&qn={quality}&fnval=4048"
        response = requests.get(play_url, headers=self.headers, cookies=self.cookies)
        play_data = response.json()

        if 'dash' not in play_data['data']:
            raise Exception('This video requires login cookie (SESSDATA) for HD formats')

        video_url = play_data['data']['dash']['video'][0]['base_url']
        audio_url = play_data['data']['dash']['audio'][0]['base_url']

        if progress_callback:
            progress_callback(0, 100, "Downloading video component...")
        
        video_file_temp = os.path.join(temp_dir, 'video_temp.m4s')
        audio_file_temp = os.path.join(temp_dir, 'audio_temp.m4s')

        video_file = self._download_file(video_url, video_file_temp, "Video", progress_callback, stop_event)
        if stop_event and stop_event.is_set():
            if progress_callback: progress_callback(0, 100, "Download stopped by user (video).")
            self._cleanup_temp_files(temp_dir, video_file_temp, None)
            return

        if progress_callback:
            progress_callback(0, 100, "Downloading audio component...")
        audio_file = self._download_file(audio_url, audio_file_temp, "Audio", progress_callback, stop_event)
        if stop_event and stop_event.is_set():
            if progress_callback: progress_callback(0, 100, "Download stopped by user (audio).")
            self._cleanup_temp_files(temp_dir, video_file_temp, audio_file_temp)
            return

        # Determine video output format. Default to mp4 if format is mp3 or empty.
        video_output_ext = output_format.lstrip('.').lower()
        if not video_output_ext or video_output_ext == 'mp3':
            video_output_ext = 'mp4' # Default to mp4 for video file
        
        final_video_file = os.path.join(output_dir, f"{sanitized_title}.{video_output_ext}")
        final_mp3_file = os.path.join(output_dir, f"{sanitized_title}.mp3")
        
        try:
            if progress_callback:
                progress_callback(0, 100, f"Merging video and audio to {video_output_ext.upper()}...")
            
            subprocess.run([
                ffmpeg_path, '-i', video_file, '-i', audio_file,
                '-c:v', 'copy', '-c:a', 'copy',
                final_video_file
            ], check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

            if stop_event and stop_event.is_set():
                 if progress_callback: progress_callback(0, 100, "Download stopped by user (during video merge).")
                 self._cleanup_temp_files(temp_dir, video_file, audio_file)
                 if os.path.exists(final_video_file): os.remove(final_video_file)
                 return

            if progress_callback:
                progress_callback(0, 100, "Converting audio to MP3...")

            subprocess.run([
                ffmpeg_path, '-i', audio_file, 
                '-c:a', 'libmp3lame', '-q:a', '0', 
                final_mp3_file
            ], check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if stop_event and stop_event.is_set():
                 if progress_callback: progress_callback(0, 100, "Download stopped by user (during MP3 conversion).")
                 self._cleanup_temp_files(temp_dir, video_file, audio_file)
                 if os.path.exists(final_video_file): os.remove(final_video_file)
                 if os.path.exists(final_mp3_file): os.remove(final_mp3_file)
                 return

        except subprocess.CalledProcessError as e:
            error_message = f"FFmpeg error during processing: {e.stderr}"
            if hasattr(e, 'cmd'): error_message += f"\nCommand: {' '.join(e.cmd)}"
            if progress_callback:
                progress_callback(0, 100, error_message)
            self._cleanup_temp_files(temp_dir, video_file, audio_file)
            if os.path.exists(final_video_file): os.remove(final_video_file)
            if os.path.exists(final_mp3_file): os.remove(final_mp3_file)
            raise Exception(error_message)
        finally:
            self._cleanup_temp_files(temp_dir, video_file, audio_file)

        if progress_callback:
             progress_callback(100, 100, f"Download completed: {final_video_file} and {final_mp3_file}")
        else:
            print(f"Download completed: {final_video_file} and {final_mp3_file} (using {ffmpeg_path} in {output_dir})") # Added output_dir for CLI clarity

    def _cleanup_temp_files(self, temp_dir, video_file_temp_path=None, audio_file_temp_path=None):
        # video_file_temp_path and audio_file_temp_path are the paths in the temp_dir
        if video_file_temp_path and os.path.exists(video_file_temp_path):
            os.remove(video_file_temp_path)
        if audio_file_temp_path and os.path.exists(audio_file_temp_path):
            os.remove(audio_file_temp_path)
        
        # Attempt to remove temp_dir if it exists and is empty
        if os.path.exists(temp_dir):
            try:
                if not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
                # else: # Optionally log or handle if temp dir is not empty after cleanup
                #    print(f"Warning: Temp directory {temp_dir} is not empty after cleanup.")
            except OSError as e:
                # print(f"Error removing temp directory {temp_dir}: {e}") # Optional logging
                pass

    def _download_file(self, url, filename, file_type_label="File", progress_callback=None, stop_event=None):
        response = requests.get(url, headers=self.headers, cookies=self.cookies, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        use_tqdm = progress_callback is None
        
        progress_bar_desc = f"{file_type_label}: {os.path.basename(filename)}"

        with open(filename, 'wb') as f:
            if use_tqdm:
                with tqdm(
                    desc=progress_bar_desc,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for data in response.iter_content(chunk_size=8192):
                        if stop_event and stop_event.is_set():
                            if progress_callback: progress_callback(downloaded_size, total_size, f"{file_type_label} download stopped.")
                            else: print(f"\n{file_type_label} download stopped.")
                            raise InterruptedError(f"{file_type_label} download stopped by user.")
                        size = f.write(data)
                        bar.update(size)
                        downloaded_size += size
            else:
                for data in response.iter_content(chunk_size=8192):
                    if stop_event and stop_event.is_set():
                        progress_callback(downloaded_size, total_size, f"{file_type_label} download stopped.")
                        raise InterruptedError(f"{file_type_label} download stopped by user.")
                    size = f.write(data)
                    downloaded_size += size
                    if progress_callback:
                        percentage = int((downloaded_size / total_size) * 100) if total_size > 0 else 0
                        progress_callback(percentage, 100, f"Downloading {file_type_label}: {downloaded_size // 1024}KB / {total_size // 1024}KB")
        
        if progress_callback and not (stop_event and stop_event.is_set()):
            progress_callback(100, 100, f"{file_type_label} download finished.")

        return filename

def extract_bvid(url):
    # Match various URL formats and direct BVid
    match = re.search(r'(BV[0-9A-Za-z]{10})', url)
    if not match:
        if url.startswith('BV') and len(url) == 12:
            return url
        raise ValueError('Invalid URL format. Examples:\nhttps://www.bilibili.com/video/BV1xx411c7mh\nhttps://b23.tv/BV1xx411c7mh\nOr direct BVid: BV1xx411c7mh')
    return match.group(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bilibili Video Downloader')
    parser.add_argument('video_url', help='Bilibili video URL or BVid (e.g. https://www.bilibili.com/video/BV1xx411c7mh or BV1xx411c7mh)')
    parser.add_argument('-q', '--quality', type=int, default=80,
                       help='Video quality (default: 80)')
    parser.add_argument('-f', '--format', default='mp4',
                       help='Output format (default: mp4)')
    parser.add_argument('--sessdata', help='Bilibili login cookie SESSDATA')
    parser.add_argument('--ffmpeg_path', default='ffmpeg', help='Path to ffmpeg executable')
    parser.add_argument('--download_path', default=None, help='Base directory for downloads (e.g., ~/Downloads)') # CLI arg for download path
    
    args = parser.parse_args()
    
    # Expand ~ for download_path if provided for CLI
    cli_download_path = None
    if args.download_path:
        cli_download_path = os.path.expanduser(args.download_path)

    downloader = BilibiliDownloader(args.sessdata)
    bvid = extract_bvid(args.video_url)
    downloader.download_video(bvid, args.quality, args.format, ffmpeg_path=args.ffmpeg_path, custom_output_base_path=cli_download_path)