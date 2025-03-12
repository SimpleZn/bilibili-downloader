import requests
import argparse
import json
import subprocess
import os
import re
from tqdm import tqdm
import urllib.parse

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

    def download_video(self, bvid, quality=80, output_format='mp4'):
        video_info = self.get_video_info(bvid)
        print(f"Downloading: {video_info['title']}")

        sanitized_title = self.sanitize_folder_name(video_info['title'])
        output_dir = os.path.join('output', sanitized_title)
        os.makedirs(output_dir, exist_ok=True)
        temp_dir = os.path.join(output_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Get playback URL
        play_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={video_info['cid']}&qn={quality}&fnval=4048"
        response = requests.get(play_url, headers=self.headers, cookies=self.cookies)
        play_data = response.json()

        if 'dash' not in play_data['data']:
            raise Exception('This video requires login cookie (SESSDATA) for HD formats')

        # Extract video/audio URLs
        video_url = play_data['data']['dash']['video'][0]['base_url']
        audio_url = play_data['data']['dash']['audio'][0]['base_url']

        # Download video and audio components
        video_file = self._download_file(video_url, os.path.join(temp_dir, 'video_temp.m4s'))
        audio_file = self._download_file(audio_url, os.path.join(temp_dir, 'audio_temp.m4s'))

        # Merge streams using FFmpeg
        output_file = os.path.join(output_dir, f"{sanitized_title}.{output_format}")
        mp3_file = os.path.join(output_dir, f"{sanitized_title}.mp3")
        subprocess.run([
            'ffmpeg', '-i', video_file, '-i', audio_file,
            '-c', 'copy', output_file
        ], check=True)

        # Convert to MP3
        subprocess.run([
            'ffmpeg', '-i', audio_file,
            '-c:a', 'libmp3lame', '-q:a', '0', mp3_file
        ], check=True)

        # Cleanup temporary files
        if os.path.exists(video_file):
            os.remove(video_file)
        if os.path.exists(audio_file):
            os.remove(audio_file)
        # Remove temp directory
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        print(f"\nDownload completed: {output_file} and {mp3_file}")

    def _download_file(self, url, filename):
        response = requests.get(url, headers=self.headers, cookies=self.cookies, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        with open(filename, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)

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
    
    args = parser.parse_args()
    
    downloader = BilibiliDownloader(args.sessdata)
    bvid = extract_bvid(args.video_url)
    downloader.download_video(bvid, args.quality, args.format)