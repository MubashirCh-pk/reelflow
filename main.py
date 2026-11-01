
import os
import threading
from urllib.parse import urlparse

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar

import yt_dlp


class ReelFlowApp(App):

    def build(self):
        self.title = "ReelFlow"

        # Main layout
        root = BoxLayout(
            orientation="vertical",
            padding=dp(22),
            spacing=dp(16)
        )

        # Background color
        with root.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(rgba=get_color_from_hex("#10101A"))
            self.background = Rectangle(
                pos=root.pos,
                size=root.size
            )

        root.bind(pos=self.update_background,
                  size=self.update_background)

        # App title
        title = Label(
            text="ReelFlow",
            font_size="34sp",
            bold=True,
            color=get_color_from_hex("#A78BFA"),
            size_hint_y=None,
            height=dp(65)
        )
        root.add_widget(title)

        # Subtitle
        subtitle = Label(
            text="Instagram Reels Downloader",
            font_size="16sp",
            color=get_color_from_hex("#D1D5DB"),
            size_hint_y=None,
            height=dp(35)
        )
        root.add_widget(subtitle)

        # URL input field
        self.url_input = TextInput(
            hint_text="Paste Instagram Reel link here...",
            multiline=False,
            size_hint_y=None,
            height=dp(55),
            font_size="15sp",
            padding=[dp(12), dp(16)],
            background_normal="",
            background_active="",
            background_color=get_color_from_hex("#242438"),
            foreground_color=get_color_from_hex("#FFFFFF"),
            hint_text_color=get_color_from_hex("#9999AA"),
            cursor_color=get_color_from_hex("#A78BFA")
        )
        root.add_widget(self.url_input)

        # Download button
        self.download_button = Button(
            text="DOWNLOAD REEL",
            size_hint_y=None,
            height=dp(55),
            font_size="17sp",
            bold=True,
            background_normal="",
            background_down="",
            background_color=get_color_from_hex("#7C3AED"),
            color=get_color_from_hex("#FFFFFF")
        )

        self.download_button.bind(
            on_release=self.start_download
        )
        root.add_widget(self.download_button)

        # Progress bar
        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(12)
        )
        root.add_widget(self.progress)

        # Status message
        self.status_label = Label(
            text="Ready to download",
            font_size="14sp",
            color=get_color_from_hex("#D1D5DB"),
            size_hint_y=None,
            height=dp(65),
            halign="center",
            valign="middle"
        )
        self.status_label.bind(
            size=self.update_status_text
        )
        root.add_widget(self.status_label)

        # Download location
        self.location_label = Label(
            text="Videos are saved in ReelFlow app storage.",
            font_size="12sp",
            color=get_color_from_hex("#9999AA"),
            size_hint_y=None,
            height=dp(55),
            halign="center",
            valign="middle"
        )
        self.location_label.bind(
            size=self.update_location_text
        )
        root.add_widget(self.location_label)

        # Footer
        footer = Label(
            text="ReelFlow  |  Version 1.0",
            font_size="11sp",
            color=get_color_from_hex("#777788"),
            size_hint_y=None,
            height=dp(30)
        )
        root.add_widget(footer)

        return root

    def update_background(self, instance, value):
        self.background.pos = instance.pos
        self.background.size = instance.size

    def update_status_text(self, instance, value):
        instance.text_size = value

    def update_location_text(self, instance, value):
        instance.text_size = value

    # Check Instagram URL
    def is_valid_instagram_url(self, url):

        if not url:
            return False

        if "://" not in url:
            url = "https://" + url

        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()

            allowed_hosts = {
                "instagram.com",
                "www.instagram.com",
                "m.instagram.com"
            }

            valid_path = (
                parsed.path.startswith("/reel/") or
                parsed.path.startswith("/reels/")
            )

            return (
                parsed.scheme == "https"
                and host in allowed_hosts
                and valid_path
            )

        except Exception:
            return False

    # Start downloading
    def start_download(self, instance):

        url = self.url_input.text.strip()

        if not self.is_valid_instagram_url(url):
            self.status_label.text = (
                "Please enter a valid Instagram Reel link."
            )
            return

        if "://" not in url:
            url = "https://" + url

        self.progress.value = 0
        self.download_button.disabled = True
        self.download_button.text = "Downloading..."
        self.status_label.text = "Connecting to Instagram..."

        threading.Thread(
            target=self.download_video,
            args=(url,),
            daemon=True
        ).start()

    # Download progress
    def progress_hook(self, data):

        if data["status"] == "downloading":

            downloaded = data.get("downloaded_bytes", 0)

            total = (
                data.get("total_bytes")
                or data.get("total_bytes_estimate")
            )

            if total:
                percentage = downloaded / total * 100
            else:
                percentage = 0

            Clock.schedule_once(
                lambda dt, p=percentage:
                self.update_progress(p), 0
            )

        elif data["status"] == "finished":

            Clock.schedule_once(
                lambda dt:
                self.update_progress(100), 0
            )

            Clock.schedule_once(
                lambda dt:
                self.update_status("Processing video..."), 0
            )

    def update_progress(self, percentage):
        self.progress.value = percentage
        self.status_label.text = (
            f"Downloading... {percentage:.1f}%"
        )

    def update_status(self, message):
        self.status_label.text = message

    # Actual download function
    def download_video(self, url):

        try:
            download_folder = os.path.join(
                self.user_data_dir,
                "downloads"
            )

            os.makedirs(
                download_folder,
                exist_ok=True
            )

            options = {
                "format": "best[ext=mp4]/best",

                "outtmpl": os.path.join(
                    download_folder,
                    "%(title).80s-%(id)s.%(ext)s"
                ),

                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "cachedir": False,
                "retries": 3,
                "fragment_retries": 3,
                "socket_timeout": 20,
                "progress_hooks": [
                    self.progress_hook
                ]
            }

            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([url])

            Clock.schedule_once(
                lambda dt:
                self.download_finished(
                    True,
                    download_folder
                ), 0
            )

        except Exception as error:

            message = str(error)

            Clock.schedule_once(
                lambda dt, msg=message:
                self.download_finished(
                    False,
                    msg
                ), 0
            )

    # Show download result
    def download_finished(self, success, result):

        self.download_button.disabled = False
        self.download_button.text = "DOWNLOAD REEL"

        if success:

            self.progress.value = 100

            self.status_label.text = (
                "Download completed successfully!"
            )

            self.location_label.text = (
                "Saved inside: " + result
            )

        else:

            self.status_label.text = (
                "Download failed: " + result[:180]
            )

            self.progress.value = 0


if __name__ == "__main__":
    ReelFlowApp().run()
