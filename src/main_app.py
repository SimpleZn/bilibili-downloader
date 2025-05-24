import sys
import webbrowser
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QTextEdit, QProgressBar, QFileDialog, QInputDialog, QMainWindow, QScrollArea
from PyQt5.QtCore import QThread, pyqtSignal, QStandardPaths, Qt
from PyQt5.QtGui import QIcon
import os
import json
import traceback
import threading
import charset_normalizer # Dummy import to help py2app

# Import downloader class and bvid extraction
from src.bilibili_downloader import BilibiliDownloader, extract_bvid


CONFIG_FILE = os.path.expanduser("~/.bilibili_downloader_config.json")
DEFAULT_DOWNLOAD_PATH = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

class DownloadThread(QThread):
    progress_update_signal = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, bvid, quality, output_format, sessdata, ffmpeg_path, download_path):
        super().__init__()
        self.bvid = bvid
        self.quality = quality
        self.output_format = output_format
        self.sessdata = sessdata
        self.ffmpeg_path = ffmpeg_path
        self.download_path = download_path
        self.stop_event = threading.Event()

    def run(self):
        try:
            downloader = BilibiliDownloader(self.sessdata)
            downloader.download_video(
                self.bvid, 
                self.quality, 
                self.output_format, 
                progress_callback=self.update_progress_gui, 
                stop_event=self.stop_event,
                ffmpeg_path=self.ffmpeg_path,
                custom_output_base_path=self.download_path
            )
            if not self.stop_event.is_set():
                self.finished_signal.emit("Download completed successfully!")
            else:
                self.error_signal.emit("Download stopped by user.")
        except InterruptedError:
             self.error_signal.emit("Download stopped by user.")
        except Exception as e:
            self.error_signal.emit(f"Download failed: {str(e)}\n{traceback.format_exc()}")

    def update_progress_gui(self, current_val, total_val, message):
        self.progress_update_signal.emit(current_val, total_val, message)

    def stop(self):
        self.stop_event.set()


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilibili Downloader Settings & Control")
        self.layout = QVBoxLayout()

        # --- Settings Fields ---
        self.sessdata_label = QLabel("SESSDATA:")
        self.sessdata_input = QLineEdit()
        self.layout.addWidget(self.sessdata_label)
        self.layout.addWidget(self.sessdata_input)

        self.quality_label = QLabel("Quality (e.g., 80 for 1080p, 116 for 4K if available):")
        self.quality_input = QLineEdit()
        self.layout.addWidget(self.quality_label)
        self.layout.addWidget(self.quality_input)

        self.format_label = QLabel("Format (e.g., mp4):")
        self.format_input = QLineEdit()
        self.layout.addWidget(self.format_label)
        self.layout.addWidget(self.format_input)

        # --- FFmpeg Path Setting ---
        self.ffmpeg_path_layout = QHBoxLayout()
        self.ffmpeg_path_label = QLabel("FFmpeg Path (optional):")
        self.ffmpeg_path_input = QLineEdit()
        self.ffmpeg_path_layout.addWidget(self.ffmpeg_path_label)
        self.ffmpeg_path_layout.addWidget(self.ffmpeg_path_input)
        self.ffmpeg_browse_button = QPushButton("Browse")
        self.ffmpeg_browse_button.clicked.connect(self.browse_ffmpeg_path)
        self.ffmpeg_path_layout.addWidget(self.ffmpeg_browse_button)
        self.layout.addLayout(self.ffmpeg_path_layout)
        # --- End FFmpeg Path Setting ---

        # --- Download Path Setting ---
        self.download_path_layout = QHBoxLayout()
        self.download_path_label = QLabel("Download Path:")
        self.download_path_input = QLineEdit()
        self.download_path_layout.addWidget(self.download_path_label)
        self.download_path_layout.addWidget(self.download_path_input)
        self.download_path_browse_button = QPushButton("Browse")
        self.download_path_browse_button.clicked.connect(self.browse_download_path)
        self.download_path_layout.addWidget(self.download_path_browse_button)
        self.layout.addLayout(self.download_path_layout)
        # --- End Download Path Setting ---

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

        # --- Download Fields ---
        self.url_label = QLabel("Bilibili Video URL or BVID:")
        self.url_input = QLineEdit()
        self.layout.addWidget(self.url_label)
        self.layout.addWidget(self.url_input)

        # --- Download Controls (Button HBox) ---
        self.download_controls_layout = QHBoxLayout()
        self.download_button = QPushButton("Download Video")
        self.download_button.clicked.connect(self.start_download)
        self.download_controls_layout.addWidget(self.download_button)

        self.stop_download_button = QPushButton("Stop Download")
        self.stop_download_button.clicked.connect(self.stop_download)
        self.stop_download_button.setEnabled(False)
        self.download_controls_layout.addWidget(self.stop_download_button)
        self.layout.addLayout(self.download_controls_layout)

        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.layout.addWidget(self.progress_bar)
        
        # --- Status/Log Area ---
        self.status_label = QLabel("Status:")
        self.layout.addWidget(self.status_label)
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.layout.addWidget(self.status_output)


        self.setLayout(self.layout)
        self.load_settings()
        self.download_thread = None

    def browse_ffmpeg_path(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg Executable", "", "All Files (*);;Applications (*.app)", options=options)
        if fileName:
            # If user selects an .app bundle, try to find the executable within
            if fileName.endswith(".app"):
                potential_path = os.path.join(fileName, "Contents", "MacOS", "ffmpeg")
                if os.path.exists(potential_path) and os.access(potential_path, os.X_OK):
                    self.ffmpeg_path_input.setText(potential_path)
                    return
                else: # try common variations if direct path not found, or just set the .app path
                    base_name = os.path.splitext(os.path.basename(fileName))[0]
                    potential_path_alt = os.path.join(fileName, "Contents", "MacOS", base_name)
                    if os.path.exists(potential_path_alt) and os.access(potential_path_alt, os.X_OK):
                         self.ffmpeg_path_input.setText(potential_path_alt)
                         return
            self.ffmpeg_path_input.setText(fileName)

    def browse_download_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        # options |= QFileDialog.DontUseNativeDialog
        directory = QFileDialog.getExistingDirectory(self, 
                                                    "Select Download Directory", 
                                                    self.download_path_input.text() or DEFAULT_DOWNLOAD_PATH,
                                                    options=options)
        if directory:
            self.download_path_input.setText(directory)

    def load_settings(self):
        config = load_config()
        self.sessdata_input.setText(config.get("SESSDATA", ""))
        self.quality_input.setText(str(config.get("quality", "80")))
        self.format_input.setText(config.get("format", "mp4"))
        self.ffmpeg_path_input.setText(config.get("ffmpeg_path", "ffmpeg"))
        self.download_path_input.setText(config.get("download_path", DEFAULT_DOWNLOAD_PATH))
        self.status_output.append("Settings loaded.")
        self.progress_bar.setFormat("Idle")

    def save_settings(self):
        sessdata = self.sessdata_input.text()
        quality_text = self.quality_input.text()
        output_format = self.format_input.text()
        ffmpeg_path = self.ffmpeg_path_input.text().strip() or "ffmpeg"
        download_path = self.download_path_input.text().strip() or DEFAULT_DOWNLOAD_PATH

        if not quality_text.isdigit():
            QMessageBox.warning(self, "Input Error", "Quality must be a number.")
            return
        
        config = {
            "SESSDATA": sessdata,
            "quality": int(quality_text),
            "format": output_format,
            "ffmpeg_path": ffmpeg_path,
            "download_path": download_path
        }
        save_config(config)
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        self.status_output.append("Settings saved.")


    def start_download(self):
        video_url_or_bvid = self.url_input.text()
        if not video_url_or_bvid:
            QMessageBox.warning(self, "Input Error", "Please enter a Bilibili video URL or BVID.")
            return

        try:
            bvid = extract_bvid(video_url_or_bvid)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid URL", str(e))
            return

        current_config = load_config()
        sessdata = self.sessdata_input.text()
        quality_text = self.quality_input.text()
        output_format = self.format_input.text()
        ffmpeg_path = self.ffmpeg_path_input.text().strip() or current_config.get("ffmpeg_path", "ffmpeg")
        download_path = self.download_path_input.text().strip() or current_config.get("download_path", DEFAULT_DOWNLOAD_PATH)

        if not sessdata:
            sessdata = current_config.get("SESSDATA")
        if not sessdata:
             QMessageBox.warning(self, "Auth Error", "SESSDATA is missing. Please set it in settings or ensure it's saved.")
             return

        if not quality_text.isdigit():
            QMessageBox.warning(self, "Input Error", "Quality must be a number.")
            return
        quality = int(quality_text)


        self.status_output.clear()
        self.status_output.append(f"Preparing to download BVID: {bvid} with quality {quality}, format {output_format}.")
        self.download_button.setEnabled(False)
        self.stop_download_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p% - Starting...")

        self.download_thread = DownloadThread(bvid, quality, output_format, sessdata, ffmpeg_path, download_path)
        self.download_thread.progress_update_signal.connect(self.update_download_progress)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.error_signal.connect(self.on_download_error)
        self.download_thread.start()

    def stop_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.status_output.append("Stopping download...")
            self.download_thread.stop()
            self.stop_download_button.setEnabled(False)

    def update_download_progress(self, current_val, total_val, message):
        self.progress_bar.setValue(current_val)
        self.progress_bar.setFormat(f"%p% - {message}")
        self.status_output.append(message)
        self.status_output.verticalScrollBar().setValue(self.status_output.verticalScrollBar().maximum())

    def on_download_finished(self, message):
        self.status_output.append(message)
        QMessageBox.information(self, "Download Complete", message)
        self.download_button.setEnabled(True)
        self.stop_download_button.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Completed - %p%")

    def on_download_error(self, error_message):
        self.status_output.append(error_message)
        if "stopped by user" not in error_message.lower():
            QMessageBox.critical(self, "Download Error/Stopped", error_message)
        else:
            QMessageBox.information(self, "Download Stopped", error_message)
        self.download_button.setEnabled(True)
        self.stop_download_button.setEnabled(False)
        if "stopped" in error_message.lower():
             self.progress_bar.setFormat(f"Stopped - {error_message.splitlines()[0]}")
        else:
             self.progress_bar.setFormat("Error - %p%")


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilibili Authorization")
        self.layout = QVBoxLayout()

        self.auth_label = QLabel("SESSDATA cookie is required. Please log in to bilibili.com and paste the SESSDATA cookie value below.")
        self.layout.addWidget(self.auth_label)

        self.open_bilibili_button = QPushButton("Open Bilibili Login")
        self.open_bilibili_button.clicked.connect(self.open_bilibili)
        self.layout.addWidget(self.open_bilibili_button)
        
        self.sessdata_input_label = QLabel("Paste SESSDATA here:")
        self.sessdata_input = QLineEdit()
        self.layout.addWidget(self.sessdata_input_label)
        self.layout.addWidget(self.sessdata_input)

        self.submit_button = QPushButton("Submit SESSDATA")
        self.submit_button.clicked.connect(self.submit_sessdata)
        self.layout.addWidget(self.submit_button)

        self.setLayout(self.layout)
        self.settings_window = None


    def open_bilibili(self):
        webbrowser.open("https://passport.bilibili.com/login")

    def submit_sessdata(self):
        sessdata = self.sessdata_input.text()
        if not sessdata:
            QMessageBox.warning(self, "Input Error", "SESSDATA cannot be empty.")
            return
        
        config = load_config()
        config["SESSDATA"] = sessdata
        if "quality" not in config:
            config["quality"] = 80 
        if "format" not in config:
            config["format"] = "mp4"
        if "ffmpeg_path" not in config:
            config["ffmpeg_path"] = "ffmpeg"
        if "download_path" not in config:
            config["download_path"] = DEFAULT_DOWNLOAD_PATH
        save_config(config)
        QMessageBox.information(self, "Authorization Successful", "SESSDATA saved. You can now use the downloader.")
        self.close()
        self.open_settings_page()

    def open_settings_page(self):
        self.settings_window = SettingsWindow()
        self.settings_window.show()


def main():
    app = QApplication(sys.argv)
    config = load_config()

    if not config.get("SESSDATA"):
        auth_window = AuthWindow()
        auth_window.show()
    else:
        settings_window = SettingsWindow()
        settings_window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 