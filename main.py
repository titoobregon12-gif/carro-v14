# CARRO PRO v14 - SIGUE ACTIVO AL CERRAR
# Necesitas 2 archivos: main.py + service.py en carpeta service/

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform as kivy_platform
import json, math, time
from datetime import date
from pathlib import Path
from collections import deque

try:
    from plyer import gps, notification, accelerometer
    HAS_PLYER = True
except:
    HAS_PLYER = False

ARCHIVO = Path.home() / "datos_final.json"
PRECIO = 4.5
VELOCIDAD_MINIMA_CARRO = 8.0
VELOCIDAD_MAXIMA_CAMINANDO = 6.5
UMBRAL_VIBRACION = 0.7

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    import math
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def cargar():
    if ARCHIVO.exists():
        try:
            with open(ARCHIVO, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"km":0, "km_gps":0, "gas":5.0, "carreras":0, "ingreso":0, "gastado":0, "aceite":100, "bateria":100, "rotula":100, "terminal":100, "pastilla":100, "llanta":100, "por_dia":{}, "motor":False, "en_marcha":False, "servicio_activo":False}

def guardar(data):
    try:
        with open(ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except: pass

class CarroV14(App):
    def build(self):
        self.data = cargar()
        self.vel = 0
        self.motor = self.data.get("motor", False)
        self.en_marcha = self.data.get("en_marcha", False)
        self.gps_on = False
        self.last_lat = None
        self.last_lon = None
        self.acc_buffer = deque(maxlen=15)
        self.ultima_vibracion = time.time()
        self.vibrando = False
        self.vibracion_actual = 0.0
        self.acc_activo = False
        self.velocidades_recientes = deque(maxlen=5)
        self.caminando = False
        self.servicio_activo = False

        root = BoxLayout(orientation='vertical')
        scroll = ScrollView(do_scroll_x=False, bar_width=20)
        content = BoxLayout(orientation='vertical', padding=12, spacing=12, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        content.add_widget(Label(text="🔋 V14 - FONDO ACTIVO", size_hint_y=None, height=35, font_size=15, bold=True, color=(0,1,0.5,1)))

        self.btn_motor = Button(text="● MOTOR ENCENDIDO" if self.motor else "● MOTOR APAGADO", background_color=(0.18,0.49,0.19,1) if self.motor else (0.8,0.2,0.2,1), size_hint_y=None, height=80, font_size=24, bold=True)
        self.btn_motor.bind(on_press=self.toggle_motor)
        content.add_widget(self.btn_motor)

        self.btn_marcha = Button(text="🚗 EN MARCHA" if self.en_marcha else "🅿️ PARADO", background_color=(0.08,0.39,0.75,1) if self.en_marcha else (0.3,0.3,0.3,1), size_hint_y=None, height=70, font_size=20, bold=True)
        self.btn_marcha.bind(on_press=self.toggle_marcha)
        content.add_widget(self.btn_marcha)

        self.btn_gps = Button(text="📡 GPS REAL", background_color=(0.1,0.5,0.9,1), size_hint_y=None, height=60, font_size=18, bold=True)
        self.btn_gps.bind(on_press=self.toggle_gps)
        content.add_widget(self.btn_gps)

        # BOTON SERVICIO - LO NUEVO
        self.btn_servicio = Button(text="▶️ ACTIVAR SERVICIO FONDO", background_color=(0.9,0.5,0,1), size_hint_y=None, height=70, font_size=18, bold=True)
        self.btn_servicio.bind(on_press=self.toggle_servicio)
        content.add_widget(self.btn_servicio)

        self.lbl_info = Label(text="Activa el servicio para que siga al cerrar", size_hint_y=None, height=45, font_size=12, bold=True, color=(1,0.8,0,1))
        content.add_widget(self.lbl_info)

        self.lbl_vibra = Label(text="📳 VIBRACION: --", font_size=16, bold=True, size_hint_y=None, height=30, color=(1,1,0,1))
        content.add_widget(self.lbl_vibra)
        self.lbl_modo = Label(text="🚶 MODO: --", font_size=16, bold=True, size_hint_y=None, height=30, color=(0,0.8,1,1))
        content.add_widget(self.lbl_modo)

        self.lbl_km = Label(text=f"{self.data['km']:.2f} KM", font_size=40, bold=True, size_hint_y=None, height=65)
        self.lbl_gps = Label(text=f"GPS {self.data.get('km_gps',0):.2f} KM | GAS {self.data['gas']:.1f}L", font_size=16, color=(0,1,0.5,1), size_hint_y=None, height=30)
        self.lbl_vel = Label(text="DETENIDO", font_size=24, bold=True, color=(0,0.8,1,1), size_hint_y=None, height=40)
        content.add_widget(self.lbl_km)
        content.add_widget(self.lbl_gps)
        content.add_widget(self.lbl_vel)

        # FINANZAS RAPIDO
        self.lbl_fin = Label(text=f"Carreras: {self.data['carreras']} S/{self.data['ingreso']:.0f}", font_size=16, bold=True, size_hint_y=None, height=30)
        hoy = date.today().isoformat()
        h = self.data['por_dia'].get(hoy, {"km":0})
        self.lbl_hoy = Label(text=f"HOY: {h['km']:.2f} km REAL", font_size=16, bold=True, size_hint_y=None, height=30, color=(0,0.9,1,1))
        content.add_widget(self.lbl_fin)
        content.add_widget(self.lbl_hoy)

        scroll.add_widget(content)
        root.add_widget(scroll)

        Clock.schedule_interval(self.ui, 0.5)
        Clock.schedule_interval(self.check_auto_pause, 1)
        Clock.schedule_interval(self.auto_guardar, 2)
        self.iniciar_acelerometro()
        
        # Si ya tenia servicio activo antes, reactivarlo
        if self.data.get("servicio_activo"):
            Clock.schedule_once(lambda dt: self.toggle_servicio(), 1)

        return root

    def iniciar_acelerometro(self):
        if not HAS_PLYER: return
        try:
            accelerometer.enable()
            self.acc_activo = True
            Clock.schedule_interval(self.leer_acelerometro, 0.15)
        except: pass

    def leer_acelerometro(self, dt):
        if not self.acc_activo: return
        try:
            acc = accelerometer.acceleration
            if acc is None or acc[0] is None: return
            x,y,z = acc[0], acc[1], acc[2]
            mag = math.sqrt(x*x + y*y + z*z)
            self.acc_buffer.append(mag)
            if len(self.acc_buffer) >= 4:
                variacion = max(self.acc_buffer) - min(self.acc_buffer)
                self.vibracion_actual = variacion
                if variacion > UMBRAL_VIBRACION:
                    self.vibrando = True
                    self.ultima_vibracion = time.time()
                else:
                    if time.time() - self.ultima_vibracion > 1.2:
                        self.vibrando = False
        except: pass

    def check_auto_pause(self, dt):
        if self.en_marcha and (time.time() - self.ultima_vibracion) > 15:
            self.en_marcha = False
            self.data['en_marcha'] = False
            self.btn_marcha.text = "🅿️ PARADO - Sin vibracion"
            self.btn_marcha.background_color = (0.3,0.3,0.3,1)
            guardar(self.data)

    # --- SERVICIO FONDO - LO NUEVO ---
    def toggle_servicio(self, *a):
        if kivy_platform != 'android':
            self.lbl_info.text = "Servicio solo funciona en Android APK"
            self.servicio_activo = not self.servicio_activo
            self.btn_servicio.text = "⏹️ DESACTIVAR FONDO" if self.servicio_activo else "▶️ ACTIVAR SERVICIO FONDO"
            return

        try:
            from jnius import autoclass
            from android import mActivity
            
            Service = autoclass('org.kivy.android.PythonService')
            # Si ya esta activo, pararlo
            if self.servicio_activo:
                Service.mService.stopSelf()
                self.servicio_activo = False
                self.data['servicio_activo'] = False
                self.btn_servicio.text = "▶️ ACTIVAR SERVICIO FONDO"
                self.btn_servicio.background_color = (0.9,0.5,0,1)
                self.lbl_info.text = "Servicio fondo DESACTIVADO"
                # quitar notificacion
                try:
                    notification.notify(title="Carro", message="Servicio detenido")
                except: pass
            else:
                # Activar servicio
                # El servicio esta en la carpeta service/
                service = autoclass('org.kivy.android.PythonService').mService
                # Iniciar nuestro servicio
                from android.storage import primary_external_storage_path
                # Usar el servicio definido en buildozer
                Service.start(mActivity, "Carro sigue activo - Marcando KM real", "Toca para volver", "")
                
                self.servicio_activo = True
                self.data['servicio_activo'] = True
                self.btn_servicio.text = "⏹️ DESACTIVAR FONDO - ACTIVO"
                self.btn_servicio.background_color = (0,0.8,0,1)
                self.lbl_info.text = "✅ SERVICIO ACTIVO - Puedes cerrar la app, seguira marcando"
                
                # Notificacion persistente
                try:
                    notification.notify(title="🚗 Carro Activo", message=f"KM {self.data['km']:.2f} - Sigue en fondo aunque cierres")
                except: pass
            
            guardar(self.data)
            
        except Exception as e:
            # Fallback sin jnius - modo simple que igual funciona si on_pause retorna True
            self.servicio_activo = not self.servicio_activo
            self.data['servicio_activo'] = self.servicio_activo
            self.btn_servicio.text = "⏹️ FONDO ACTIVO (modo simple)" if self.servicio_activo else "▶️ ACTIVAR SERVICIO FONDO"
            self.lbl_info.text = f"Modo simple activo - No cierres del todo. Error: {e}"
            guardar(self.data)

    def toggle_motor(self, *a):
        self.motor = not self.motor
        self.data['motor'] = self.motor
        self.btn_motor.text = "● MOTOR ENCENDIDO" if self.motor else "● MOTOR APAGADO"
        self.btn_motor.background_color = (0.18,0.49,0.19,1) if self.motor else (0.8,0.2,0.2,1)
        if not self.motor:
            self.en_marcha = False
            self.data['en_marcha'] = False
            self.btn_marcha.text = "🅿️ PARADO"
            self.btn_marcha.background_color = (0.3,0.3,0.3,1)
        guardar(self.data)

    def toggle_marcha(self, *a):
        self.en_marcha = not self.en_marcha
        self.data['en_marcha'] = self.en_marcha
        self.btn_marcha.text = "🚗 EN MARCHA" if self.en_marcha else "🅿️ PARADO"
        self.btn_marcha.background_color = (0.08,0.39,0.75,1) if self.en_marcha else (0.3,0.3,0.3,1)
        if self.en_marcha:
            self.ultima_vibracion = time.time()
            self.velocidades_recientes.clear()
        guardar(self.data)

    def toggle_gps(self, *a):
        if not HAS_PLYER:
            self.gps_on = not self.gps_on
            return
        try:
            if not self.gps_on:
                gps.configure(on_location=self.on_gps)
                gps.start(minTime=1000, minDistance=2)
                self.gps_on = True
                self.btn_gps.text = "📡 GPS ON"
            else:
                gps.stop()
                self.gps_on = False
                self.btn_gps.text = "📡 GPS OFF"
        except Exception as e:
            self.lbl_info.text = f"GPS: {e}"

    def on_gps(self, **k):
        lat=k.get('lat'); lon=k.get('lon')
        if lat is None: return
        if self.last_lat is None:
            self.last_lat=lat; self.last_lon=lon
            return
        dist=haversine(self.last_lat, self.last_lon, lat, lon)
        if dist < 0.002 or dist > 0.4:
            if dist > 0.4:
                self.last_lat=lat; self.last_lon=lon
            return
        velocidad = dist * 3600
        if velocidad > 150: velocidad = 0
        self.velocidades_recientes.append(velocidad)
        vel_prom = sum(self.velocidades_recientes)/len(self.velocidades_recientes) if self.velocidades_recientes else velocidad
        
        es_caminata = vel_prom < VELOCIDAD_MAXIMA_CAMINANDO and vel_prom > 0.5
        if es_caminata:
            self.caminando = True
            self.vel = velocidad
            self.last_lat=lat; self.last_lon=lon
            return
        self.caminando = False
        if not self.vibrando:
            self.last_lat=lat; self.last_lon=lon
            return
        if vel_prom < VELOCIDAD_MINIMA_CARRO:
            self.last_lat=lat; self.last_lon=lon
            return
        if self.motor and self.en_marcha and self.vibrando and vel_prom >= VELOCIDAD_MINIMA_CARRO:
            self.data['km']+=dist
            self.data['km_gps']=self.data.get('km_gps',0)+dist
            hoy=date.today().isoformat()
            if hoy not in self.data['por_dia']: self.data['por_dia'][hoy]={"km":0,"ingreso":0,"gasto":0}
            self.data['por_dia'][hoy]['km']+=dist
            self.vel = vel_prom
            guardar(self.data)
        self.last_lat=lat; self.last_lon=lon

    def auto_guardar(self, dt):
        guardar(self.data)
        # Actualizar notificacion si servicio activo
        if self.servicio_activo and kivy_platform == 'android':
            try:
                notification.notify(title=f"🚗 {self.data['km']:.2f} KM | {self.vel:.0f}km/h", message="Servicio activo - Toca para volver al carro", toast=False)
            except: pass

    def ui(self, dt):
        self.lbl_km.text=f"{self.data['km']:.2f} KM"
        self.lbl_gps.text=f"GPS {self.data.get('km_gps',0):.2f} KM"
        if self.vibrando:
            self.lbl_vibra.text = f"📳 CARRO {self.vibracion_actual:.2f}"
            self.lbl_vibra.color = (0,1,0.5,1)
        else:
            self.lbl_vibra.text = f"📳 SIN VIB {int(time.time()-self.ultima_vibracion)}s"
            self.lbl_vibra.color = (1,0.3,0.3,1)
        if self.caminando:
            self.lbl_modo.text = "🚶 CAMINANDO - NO CUENTA"
            self.lbl_modo.color = (1,0.8,0,1)
        elif self.en_marcha and self.vibrando and self.vel >= VELOCIDAD_MINIMA_CARRO:
            self.lbl_modo.text = "🚗 CARRO >8km/h"
            self.lbl_modo.color = (0,1,0.5,1)
        else:
            self.lbl_modo.text = "🅿️ PARADO"
            self.lbl_modo.color = (0.8,0.8,0.8,1)
        self.lbl_vel.text=f"{self.vel:.0f} km/h" if self.vel>1 else "DETENIDO"
        self.lbl_fin.text=f"Carreras: {self.data['carreras']} S/{self.data['ingreso']:.0f}"
        hoy=date.today().isoformat()
        h=self.data['por_dia'].get(hoy,{"km":0})
        self.lbl_hoy.text=f"HOY: {h['km']:.2f} km"

    # CLAVE PARA QUE NO SE CIERRE
    def on_pause(self):
        # Retorna True = la app sigue viva en fondo
        guardar(self.data)
        return True

    def on_resume(self):
        # Cuando vuelves a abrir
        self.data = cargar()
        pass

    def on_stop(self):
        # Si el servicio esta activo, NO detener GPS
        if self.servicio_activo:
            # No detener nada, dejar que el servicio siga
            return
        try:
            if self.acc_activo: accelerometer.disable()
            if self.gps_on: gps.stop()
        except: pass
        guardar(self.data)

CarroV14().run()
