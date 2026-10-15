[app]
title = Carro Pro V14
package.name = carroprov14
package.domain = com.taxi.carroprov14
source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json
version = 14
requirements = python3,kivy==2.2.0,plyer,pyjnius,android
orientation = portrait
fullscreen = 0
android.permissions = ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_BACKGROUND_LOCATION,FOREGROUND_SERVICE,FOREGROUND_SERVICE_LOCATION,VIBRATE,WAKE_LOCK,POST_NOTIFICATIONS,INTERNET
android.api = 33
android.build_tools_version = 33.0.2
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license_agreement = True
android.wakelock = True
p4a.bootstrap = sdl2
p4a.whitelist = libffi-openssl,sqlite

[buildozer]
log_level = 2
warn_on_root = 1

[base]
p4a.branch = master
