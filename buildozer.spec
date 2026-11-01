[app]

title = ReelFlow
package.name = reelflow
package.domain = com.reelflow

source.dir = .
source.include_exts = py,kv,png,jpg,atlas
source.exclude_dirs = venv, .buildozer, bin, __pycache__

version = 1.0

requirements = python3,kivy,yt-dlp

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

