[app]

title = Mevira Keep
package.name = mevirakeep
package.domain = com.mevira.keep

source.dir = .
source.include_exts = py,png,jpg,jpeg,wav,m4a,mp3,json

version = 1.0

requirements = python3,kivy,plyer

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,RECORD_AUDIO

android.api = 35
android.minapi = 23
android.archs = arm64-v8a

[buildozer]

log_level = 2
warn_on_root = 1
