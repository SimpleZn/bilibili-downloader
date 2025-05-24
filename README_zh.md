阅读语言: [English](README.md) | [中文](README_zh.md)

# Bilibili 视频下载器 GUI

一个用于从 Bilibili.com 下载视频及其音轨的简单 GUI 应用程序。

## 功能

- 通过 URL 或 BVID 下载 Bilibili 视频。
- 同时保存视频文件（例如 MP4）和单独的 MP3 音频文件。
- GUI 设置：
    - SESSDATA cookie 用于访问高清格式和需要登录的内容。
    - 视频质量选择。
    - 视频输出格式（例如 `mp4`, `mkv` - 如果输入像 `mp3` 这样的音频格式，则默认为 `mp4`）。
    - FFmpeg 可执行文件的自定义路径。
    - 自定义下载目录（默认为系统的"下载"文件夹，文件将整理到 `[所选路径]/Bilibili_Downloads/[视频标题]/` 中）。
- 下载过程中的进度条和状态消息。
- 能够停止正在进行的下载。

## 先决条件

1.  **Python 3**: 确保已安装 Python 3。（已在 Python 3.12+ 上测试）
2.  **FFmpeg**: 此应用程序需要 FFmpeg 来合并视频/音频流并将音频转换为 MP3。
    -   **macOS (使用 Homebrew)**: `brew install ffmpeg`
    -   **其他操作系统**: 从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载并确保它在系统的 PATH 中，或者在应用程序设置中提供完整路径。

## 设置和安装

1.  **克隆仓库（如果适用）或下载文件**:
    ```bash
    # 如果你将其作为 git 仓库
    # git clone <repository_url>
    # cd <repository_directory>
    ```

2.  **创建虚拟环境 (推荐)**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Windows 上: venv\Scripts\activate
    ```

3.  **安装依赖**:
    确保你有一个 `requirements.txt` 文件，其中包含以下内容：
    ```txt
    PyQt5
    py2app
    requests
    tqdm
    ```
    然后运行：
    ```bash
    pip install -r requirements.txt
    ```

## 运行应用程序

### 选项 1: 直接从 Python 运行 (用于开发/测试)

```bash
python3 src/main_app.py
```

### 选项 2: 构建 macOS 应用程序包

1.  **创建图标 (可选但推荐)**:
    -   在项目根目录中创建一个名为 `icon.icns` 的图标文件。你可以使用在线转换器从 PNG 创建 `.icns` 文件。

2.  **构建应用程序**:
    `setup.py` 文件配置为使用 `py2app`。
    ```bash
    python3 setup.py py2app -A  # 别名模式，用于更快的开发构建
    # 对于可分发的应用程序，你可能使用：
    # python3 setup.py py2app
    ```

3.  **运行应用程序**:
    应用程序包 (`Bilibili Downloader.app`) 将在 `dist` 目录中创建。双击它以运行。

## 首次使用和设置

1.  **授权 (SESSDATA)**:
    -   首次启动时（或如果未配置 `SESSDATA`），将出现授权窗口。
    -   点击"打开 Bilibili 登录"以在浏览器中进入 Bilibili 登录页面。
    -   登录后，你需要获取 `SESSDATA` cookie：
        1.  在浏览器（例如 Chrome, Firefox）中，打开开发者工具（通常通过右键单击页面并选择"检查"或按 F12）。
        2.  转到"Application"（Chrome）或"Storage"（Firefox）选项卡。
        3.  在"Cookies"下，找到 `https://www.bilibili.com`。
        4.  找到名为 `SESSDATA` 的 cookie 并复制其"Value"。
    -   将此值粘贴到应用程序中的 SESSDATA 输入字段，然后单击"提交 SESSDATA"。

2.  **设置页面**:
    -   授权后，或在后续启动时，将出现主设置页面。
    -   **SESSDATA**: 你的 Bilibili SESSDATA cookie。
    -   **Quality (质量)**: 视频质量设置（例如 80 代表 1080p, 116 代表 4K - 如果需要，请查阅 Bilibili 标准）。
    -   **Format (格式)**: 期望的*视频*输出格式。常见选项包括 `mp4`, `mkv`, `mov`, `avi`, `flv`, `webm`。将始终单独生成 MP3 音频文件。如果在此处输入 `mp3` 等纯音频格式，视频将默认为 `mp4`。
    -   **FFmpeg Path (FFmpeg 路径)**: `ffmpeg` 可执行文件的完整路径。如果 `ffmpeg` 在你的系统 PATH 中，你可以将其保留为 `ffmpeg`。如果需要，使用"浏览"定位它。
    -   **Download Path (下载路径)**: 下载文件将保存的目录。默认为你系统的"下载"文件夹。文件将整理到 `[所选路径]/Bilibili_Downloads/[视频标题]/` 中。
    -   单击"保存设置"以保存你的首选项。这些设置存储在 `~/.bilibili_downloader_config.json` 中。

3.  **重置设置**:
    -   如果需要将所有应用程序设置重置为默认值，可以通过删除配置文件来完成。
    -   关闭 Bilibili 下载器应用程序。
    -   打开终端并运行以下命令：
        ```bash
        rm -f ~/.bilibili_downloader_config.json
        ```
    -   下次启动应用程序时，它将如同首次启动一样，并且在你保存设置时将创建一个新的默认配置文件。

## 下载视频

1.  在"Bilibili 视频 URL 或 BVID"字段中输入 Bilibili 视频 URL（例如 `https://www.bilibili.com/video/BVxxxxxxxxxx`）或仅输入 BVID（例如 `BVxxxxxxxxxx`）。
2.  确保你的设置（质量、格式、路径）已按需配置。
3.  单击"下载视频"。
4.  进度条和状态区域将显示下载进度。
5.  你可以单击"停止下载"以取消正在进行的下载。
6.  完成的文件（视频和 MP3 音频）将在你指定的下载路径下的 `Bilibili_Downloads/[视频标题]/` 中。

## 注意事项

- 如果未配置或无法访问下载路径设置，项目根目录中的 `output` 文件夹将用作后备（主要用于 CLI 脚本使用）。
- 应用程序会在每个视频的下载目录中创建一个 `temp` 子文件夹用于存放临时文件，这些文件在下载完成后（或出错/停止时）会被清理。

## 许可证
MIT 许可证 