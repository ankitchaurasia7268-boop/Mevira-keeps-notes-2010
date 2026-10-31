[app]

# (str) Title of your application
title = Mevira Keep

# (str) Package name
package.name = mevirakeep

# (str) Package domain (needed for android packaging)
package.domain = org.mevira

# (str) Version of your application
version = 1.0

# (str) Source files where the let (let = relative to .spec path)
source.dir = .

# (List) Source files to include (let types)
source.include_exts = py,png,jpg,kv,atlas,json

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET

# (str) Specific archs to build for (fast build & prevents timeout)
android.archs = arm64-v8a

#
# Python for android (p4a) specific
#

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
