from setuptools import setup

APP = ['src/main_app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['requests', 'tqdm', 'PyQt5', 'src', 'charset_normalizer'],
    'iconfile': 'src/bilibili_downloader.icns',
    'plist': {
        'CFBundleName': 'Bilibili Downloader',
        'CFBundleDisplayName': 'Bilibili Downloader',
        'CFBundleGetInfoString': 'Downloads videos from Bilibili',
        'CFBundleIdentifier': 'com.example.bilibilidownloader',
        'CFBundleVersion': '0.1.3',
        'CFBundleShortVersionString': '0.1.3',
        'NSHumanReadableCopyright': 'Copyright © 2023 Your Name. All rights reserved.'
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 