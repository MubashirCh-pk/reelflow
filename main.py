%%writefile main.py
import os
import threading

from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.utils import platform

import yt_dlp

Window.clearcolor = (0.09, 0.10, 0.14, 1)

KV = """
BoxLayout:
    orientation: "vertical"
    padding: dp(20)
    spacing: dp(14)

    BoxLayout:
        size_hint_y: None
        height: dp(60)
        spacing: dp(10)
        Label:
            text: "[b]ReelFlow[/b]"
            markup: True
            font_size: "28sp"
            color: 0.55, 0.36, 0.96, 1
            halign: "left"
            text_size: self.size
            valign: "middle"

    Label:
        text: "Paste an Instagram video link below"
        font_size: "14sp"
        color: 0.63, 0.63, 0.67, 1
        size_hint_y: None
        height: dp(30)

    TextInput:
        id: url_input
        hint_text: "https://www.instagram.com/reel/..."
        multiline: False
        size_hint_y: None
        height: dp(52)
        font_size: "15sp"
        background_color: 0.06, 0.07, 0.10, 1
        foreground_color: 1, 1, 1, 1
        hint_text_color: 0.45, 0.45, 0.5, 1
        cursor_color: 0.55, 0.36, 0.96, 1
        padding: dp(14), dp(14)

    Button:
        id: dl_btn
        text: app.button_text
        disabled: app.busy
        size_hint_y: None
        height: dp(52)
        font_size: "16sp"
        bold: True
        background_normal: ""
        background_color: 0.43, 0.36, 0.98, 1
        on_release: app.start_download(url_input.text)

    BoxLayout:
        size_hint_y: None
        height: dp(24)
        Label:
            text: app.status
            font_size: "13sp"
            color: 0.83, 0.83, 0.85, 1
            halign: "left"
            text_size: self.size
        Label:
            text: app.percent_text
            font_size: "13sp"
            bold: True
            color: 0.65, 0.55, 0.98, 1
            halign: "right"
            text_size: self.size
            size_hint_x: None
            width: dp(70)

    ProgressBar:
        max: 100
        value: app.progress
        size_hint_y: None
        height: dp(12)

    Label:
        text: "Saving to:\\n" + app.folder
        font_size: "12sp"
        color: 0.63, 0.63, 0.67, 1
        halign: "left"
        valign: "top"
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] + dp(10)

    Widget:
"""


class ReelFlowApp(App):
    status = StringProperty("Ready to download")
    percent_text = StringProperty("0%")
    progress = NumericProperty(0)
    button_text = StringProperty("Download Reel")
    busy = NumericProperty(0)
    folder = StringProperty("")

    def build(self):
        self.title = "ReelFlow"
        self.folder = self._pick_folder()
        return Builder.load_string(KV)

    # ---------- storage ----------
    def _pick_folder(self):
        if platform == "android":
            from android.permissions import Permission, request_permissions
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
            ])
            path = "/storage/emulated/0/Download/ReelFlow"
        else:
            path = os.path.join(os.path.expanduser("~"), "Downloads", "ReelFlow")
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except Exception:
            # Fallback: app-private storage (always writable)
            return self.user_data_dir

    def _writable_folder(self):
        try:
            os.makedirs(self.folder, exist_ok=True)
            test = os.path.join(self.folder, ".write_test")
            with open(test, "w") as f:
                f.write("ok")
            os.remove(test)
            return self.folder
        except Exception:
            self.set_folder(self.user_data_dir)
            return self.user_data_dir

    @mainthread
    def set_folder(self, path):
        self.folder = path

    # ---------- UI updates (thread-safe) ----------
    @mainthread
    def set_status(self, text):
        self.status = text

    @mainthread
    def set_progress(self, percent):
        self.progress = percent
        self.percent_text = f"{percent:.1f}%"

    @mainthread
    def set_busy(self, busy):
        self.busy = 1 if busy else 0
        self.button_text = "Downloading..." if busy else "Download Reel"

    # ---------- download ----------
    def _hook(self, data):
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            done = data.get("downloaded_bytes", 0)
            if total:
                self.set_progress(done / total * 100)
                self.set_status("Downloading your video...")
        elif data.get("status") == "finished":
            self.set_progress(100)

    def start_download(self, url):
        url = url.strip()
        if not url:
            self.set_status("Please paste an Instagram link.")
            return
        if "instagram.com" not in url.lower():
            self.set_status("Please enter a valid Instagram URL.")
            return

        folder = self._writable_folder()
        self.set_busy(True)
        self.set_progress(0)
        self.set_status("Connecting to Instagram...")
        threading.Thread(target=self._worker, args=(url, folder), daemon=True).start()

    def _worker(self, url, folder):
        options = {
            "outtmpl": os.path.join(folder, "%(title).80s.%(ext)s"),
            # No ffmpeg on Android, so only single-file formats
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "progress_hooks": [self._hook],
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
            self.set_status("Download completed!")
        except Exception as error:
            self.set_status("Failed: private, unavailable, or login required.\n" + str(error)[:200])
        finally:
            self.set_busy(False)


if __name__ == "__main__":
    ReelFlowApp().run()
