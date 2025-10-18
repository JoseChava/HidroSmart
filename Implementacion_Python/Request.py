import requests
import json
import time
from datetime import datetime
import os
import serial
import tkinter as tk
from tkinter import ttk, messagebox

ARDUINO_PORT = 'COM3'
BAUD_RATE = 115200
DEBUG_MODE = True

class HydroSmart:
    def __init__(self):
        self.debug_mode = DEBUG_MODE
        self.arduino_com = ComunicacionArduino()
        self.config_manager = ConfigManager()
        
    def debug_log(self, mensaje):
        if self.debug_mode:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f" [{timestamp}] {mensaje}")

    def obtener_clima(self):
        self.debug_log("Obteniendo probabilidad de lluvia...")
        api_key = "10ab96a1dec2098d86096f30091ee55f"
        lat, lon = 9.859018909982325, -83.91360769948011
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es"
            respuesta = requests.get(url, timeout=10)
            datos = respuesta.json()
            
            prob_lluvia = 0
            if 'rain' in datos and '1h' in datos['rain']:
                prob_lluvia = min(100, datos['rain']['1h'] * 20)
            elif datos['weather'][0]['main'].lower() in ['rain', 'drizzle', 'thunderstorm']:
                prob_lluvia = 80
            
            return {
                "timestamp": datetime.now().isoformat(),
                "clima": {
                    "probabilidad_lluvia": round(prob_lluvia),
                    "condicion_principal": datos["weather"][0]["main"],
                },
                "configuracion_riego": self.config_manager.obtener_configuracion()
            }
        except Exception as e:
            self.debug_log(f"Error clima: {e}")
            return None

    def ejecutar(self):
        self.debug_log("=== INICIANDO HYDROSMART ===")
        
        print("¿Desea configurar los horarios de riego? (s/n)")
        respuesta = input().lower().strip()
        
        if respuesta == 's':
            ConfiguradorHorarios(tk.Tk())
        
        arduino_activo = self.arduino_com.conectar()
        
        print(f"\nHYDROSMART INICIADO")
        print(f"Arduino: {'CONECTADO' if arduino_activo else 'DESCONECTADO'}")
        print("Ctrl+C para detener\n")
        
        contador = 0
        try:
            while True:
                contador += 1
                print(f"\n Ejecución #{contador}")
                
                datos_clima = self.obtener_clima()
                if datos_clima:
                    if arduino_activo:
                        if not self.arduino_com.enviar_datos(datos_clima):
                            self.debug_log("Falló Arduino")
                            arduino_activo = False
                    
                    clima = datos_clima['clima']
                    config = datos_clima['configuracion_riego']
                    hora_actual = datetime.now().strftime("%H:%M")
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    
                    print(f"  Fecha: {fecha_actual}")
                    print(f"  Hora actual: {hora_actual}")
                    print(f"  Probabilidad de lluvia: {clima['probabilidad_lluvia']}%")
                    print(f"  Condición: {clima['condicion_principal']}")
                    print(f"  Condición riego: Lluvia < 70% ({clima['probabilidad_lluvia']}%)")
                    print(f"  Horarios: Z1({config['i_hora_riego_z1']}-{config['f_hora_riego_z1']}) | "
                          f"Z2({config['i_hora_riego_z2']}-{config['f_hora_riego_z2']}) | "
                          f"Z3({config['i_hora_riego_z3']}-{config['f_hora_riego_z3']})")
                    
                    freq_z1 = self._get_frecuencia_texto(config['dias_riego_z1'])
                    freq_z2 = self._get_frecuencia_texto(config['dias_riego_z2'])
                    freq_z3 = self._get_frecuencia_texto(config['dias_riego_z3'])
                    
                    print(f"  Frecuencia riego: Z1({freq_z1}) | Z2({freq_z2}) | Z3({freq_z3})")
                    print(f"  Umbrales humedad:")
                    print(f"    Z1: Activar <{config['humedad_minima_z1']}% | Detener >={config['humedad_maxima_z1']}%")
                    print(f"    Z2: Activar <{config['humedad_minima_z2']}% | Detener >={config['humedad_maxima_z2']}%")
                    print(f"    Z3: Activar <{config['humedad_minima_z3']}% | Detener >={config['humedad_maxima_z3']}%")
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\nDetenido por usuario")
        finally:
            self.arduino_com.cerrar()

    def _get_frecuencia_texto(self, dias_config):
        if dias_config == -1:
            return "NUNCA"
        elif dias_config == 0:
            return "DIARIO"
        elif dias_config == 1:
            return "CADA_2_DÍAS"
        elif dias_config == 2:
            return "CADA_3_DÍAS"
        else:
            return f"CADA_{dias_config + 1}_DÍAS"

class ConfigManager:
    def __init__(self):
        self.config_file = "config_riego.json"
    
    def obtener_configuracion(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
        
        return {
            "i_hora_riego_z1": "15:00",
            "f_hora_riego_z1": "20:30", 
            "i_hora_riego_z2": "15:00",
            "f_hora_riego_z2": "20:30",
            "i_hora_riego_z3": "20:00",
            "f_hora_riego_z3": "20:30",
            "dias_riego_z1": 1,  # 1 = cada 2 días 
            "dias_riego_z2": 1,  # 1 = cada 2 días
            "dias_riego_z3": 2,  # 2 = cada 3 días
            "humedad_minima_z1": 30,
            "humedad_maxima_z1": 60,
            "humedad_minima_z2": 30,
            "humedad_maxima_z2": 60,
            "humedad_minima_z3": 30,
            "humedad_maxima_z3": 60
        }

class ConfiguradorHorarios:
    def __init__(self, root):
        self.root = root
        self.root.title("HydroSmart - Configuración de Riego")
        self.root.geometry("800x600")
        
        self.zona1_inicio = tk.StringVar(value="15:00")
        self.zona1_fin = tk.StringVar(value="20:30")
        self.zona2_inicio = tk.StringVar(value="15:00")
        self.zona2_fin = tk.StringVar(value="20:30")
        self.zona3_inicio = tk.StringVar(value="20:00")
        self.zona3_fin = tk.StringVar(value="20:30")
        
        self.dias_riego_z1 = tk.StringVar(value="1")
        self.dias_riego_z2 = tk.StringVar(value="1")
        self.dias_riego_z3 = tk.StringVar(value="2")
        
        self.humedad_minima_z1 = tk.StringVar(value="30")
        self.humedad_maxima_z1 = tk.StringVar(value="60")
        self.humedad_minima_z2 = tk.StringVar(value="30")
        self.humedad_maxima_z2 = tk.StringVar(value="60")
        self.humedad_minima_z3 = tk.StringVar(value="30")
        self.humedad_maxima_z3 = tk.StringVar(value="60")
        
        self.crear_interfaz()
        self.root.mainloop()
        
    def crear_interfaz(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        titulo = ttk.Label(main_frame, text="Configuración de Riego por Zona", 
                          font=("Arial", 12, "bold"))
        titulo.grid(row=0, column=0, columnspan=7, pady=(0, 20))
        
        ttk.Label(main_frame, text="Zona").grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(main_frame, text="Horario Inicio").grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(main_frame, text="Horario Fin").grid(row=1, column=2, padx=5, pady=5)
        ttk.Label(main_frame, text="Frecuencia").grid(row=1, column=3, padx=5, pady=5)
        ttk.Label(main_frame, text="Humedad Mín").grid(row=1, column=4, padx=5, pady=5)
        ttk.Label(main_frame, text="Humedad Máx").grid(row=1, column=5, padx=5, pady=5)
        
        ttk.Label(main_frame, text="", width=8).grid(row=2, column=0, padx=5, pady=2)
        ttk.Label(main_frame, text="HH:MM", font=("Arial", 7), foreground="gray").grid(row=2, column=1, padx=5, pady=2)
        ttk.Label(main_frame, text="HH:MM", font=("Arial", 7), foreground="gray").grid(row=2, column=2, padx=5, pady=2)
        ttk.Label(main_frame, text="-1=Nunca, 0=Diario, 1=Cada 2d...", 
                 font=("Arial", 6), foreground="blue").grid(row=2, column=3, padx=5, pady=2)
        ttk.Label(main_frame, text="% activar", font=("Arial", 7), foreground="gray").grid(row=2, column=4, padx=5, pady=2)
        ttk.Label(main_frame, text="% detener", font=("Arial", 7), foreground="gray").grid(row=2, column=5, padx=5, pady=2)
        
        ttk.Label(main_frame, text="Zona 1", font=("Arial", 9, "bold")).grid(row=3, column=0, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.zona1_inicio, width=8).grid(row=3, column=1, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.zona1_fin, width=8).grid(row=3, column=2, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.dias_riego_z1, width=5).grid(row=3, column=3, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.humedad_minima_z1, width=5).grid(row=3, column=4, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.humedad_maxima_z1, width=5).grid(row=3, column=5, padx=5, pady=8)
        
        ttk.Label(main_frame, text="Zona 2", font=("Arial", 9, "bold")).grid(row=4, column=0, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.zona2_inicio, width=8).grid(row=4, column=1, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.zona2_fin, width=8).grid(row=4, column=2, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.dias_riego_z2, width=5).grid(row=4, column=3, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.humedad_minima_z2, width=5).grid(row=4, column=4, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.humedad_maxima_z2, width=5).grid(row=4, column=5, padx=5, pady=8)
        
        ttk.Label(main_frame, text="Zona 3", font=("Arial", 9, "bold")).grid(row=5, column=0, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.zona3_inicio, width=8).grid(row=5, column=1, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.zona3_fin, width=8).grid(row=5, column=2, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.dias_riego_z3, width=5).grid(row=5, column=3, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.humedad_minima_z3, width=5).grid(row=5, column=4, padx=5, pady=8)
        ttk.Entry(main_frame, textvariable=self.humedad_maxima_z3, width=5).grid(row=5, column=5, padx=5, pady=8)
        
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=6, column=0, columnspan=7, pady=30)
        
        ttk.Button(botones_frame, text="Guardar Configuración", 
                  command=self.guardar_configuracion).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones_frame, text="Cargar Configuración", 
                  command=self.cargar_configuracion).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones_frame, text="Configuración por Defecto", 
                  command=self.configuracion_defecto).pack(side=tk.LEFT, padx=5)
        
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=7, column=0, columnspan=7, pady=(10, 0))
        
        ttk.Label(info_frame, text="Formato horario: HH:MM (24 horas) | Frecuencia: -1=Nunca, 0=Diario, 1=Cada 2 días, 2=Cada 3 días...", 
                 font=("Arial", 8), foreground="gray").pack()
        ttk.Label(info_frame, text="Humedad Mínima: Activar riego cuando humedad < este valor | Humedad Máxima: Detener riego cuando humedad >= este valor", 
                 font=("Arial", 8), foreground="gray").pack()
        
    def validar_horario(self, horario):
        try:
            horas, minutos = horario.split(":")
            if 0 <= int(horas) <= 23 and 0 <= int(minutos) <= 59:
                return True
        except:
            pass
        return False
    
    def validar_dias(self, dias_str):
        try:
            dias = int(dias_str)
            # -1 = Nunca, 0 = Todos los días, 1 = Cada 2 días, 2 = Cada 3 días, etc.
            if -1 <= dias <= 365:
                return True
        except:
            pass
        return False
    
    def validar_humedad(self, humedad_str):
        try:
            humedad = int(humedad_str)
            if 0 <= humedad <= 100:
                return True
        except:
            pass
        return False
    
    def validar_rango_humedad_por_zona(self, min_str, max_str, zona):
        try:
            min_val = int(min_str)
            max_val = int(max_str)
            if min_val >= max_val:
                messagebox.showerror("Error", f"En {zona}: La humedad mínima debe ser menor que la humedad máxima")
                return False
            return True
        except:
            return False
    
    def guardar_configuracion(self):
        horarios = [
            (self.zona1_inicio.get(), "Inicio Zona 1"),
            (self.zona1_fin.get(), "Fin Zona 1"),
            (self.zona2_inicio.get(), "Inicio Zona 2"),
            (self.zona2_fin.get(), "Fin Zona 2"),
            (self.zona3_inicio.get(), "Inicio Zona 3"),
            (self.zona3_fin.get(), "Fin Zona 3")
        ]
        
        for horario, nombre in horarios:
            if not self.validar_horario(horario):
                messagebox.showerror("Error", f"Formato inválido en {nombre}: {horario}\nUse HH:MM (24 horas)")
                return
        
        dias_config = [
            (self.dias_riego_z1.get(), "Frecuencia Zona 1"),
            (self.dias_riego_z2.get(), "Frecuencia Zona 2"),
            (self.dias_riego_z3.get(), "Frecuencia Zona 3")
        ]
        
        for dias, nombre in dias_config:
            if not self.validar_dias(dias):
                messagebox.showerror("Error", f"Valor inválido en {nombre}: {dias}\nUse -1 (Nunca), 0 (Diario), 1 (Cada 2 días), etc.")
                return
        
        humedad_config = [
            (self.humedad_minima_z1.get(), self.humedad_maxima_z1.get(), "Zona 1"),
            (self.humedad_minima_z2.get(), self.humedad_maxima_z2.get(), "Zona 2"),
            (self.humedad_minima_z3.get(), self.humedad_maxima_z3.get(), "Zona 3")
        ]
        
        for min_hum, max_hum, zona in humedad_config:
            if not self.validar_humedad(min_hum):
                messagebox.showerror("Error", f"Valor inválido en Humedad Mínima {zona}: {min_hum}\nUse porcentaje entre 0 y 100")
                return
            if not self.validar_humedad(max_hum):
                messagebox.showerror("Error", f"Valor inválido en Humedad Máxima {zona}: {max_hum}\nUse porcentaje entre 0 y 100")
                return
            if not self.validar_rango_humedad_por_zona(min_hum, max_hum, zona):
                return
        
        config = self.obtener_configuracion_dict()
        try:
            with open("config_riego.json", "w") as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    def cargar_configuracion(self):
        try:
            if os.path.exists("config_riego.json"):
                with open("config_riego.json", "r") as f:
                    config = json.load(f)
                
                self.zona1_inicio.set(config["i_hora_riego_z1"])
                self.zona1_fin.set(config["f_hora_riego_z1"])
                self.zona2_inicio.set(config["i_hora_riego_z2"])
                self.zona2_fin.set(config["f_hora_riego_z2"])
                self.zona3_inicio.set(config["i_hora_riego_z3"])
                self.zona3_fin.set(config["f_hora_riego_z3"])
                self.dias_riego_z1.set(str(config["dias_riego_z1"]))
                self.dias_riego_z2.set(str(config["dias_riego_z2"]))
                self.dias_riego_z3.set(str(config["dias_riego_z3"]))
                self.humedad_minima_z1.set(str(config["humedad_minima_z1"]))
                self.humedad_maxima_z1.set(str(config["humedad_maxima_z1"]))
                self.humedad_minima_z2.set(str(config["humedad_minima_z2"]))
                self.humedad_maxima_z2.set(str(config["humedad_maxima_z2"]))
                self.humedad_minima_z3.set(str(config["humedad_minima_z3"]))
                self.humedad_maxima_z3.set(str(config["humedad_maxima_z3"]))
                
                messagebox.showinfo("Éxito", "Configuración cargada correctamente")
            else:
                messagebox.showinfo("Info", "No hay configuración guardada")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar: {e}")
    
    def configuracion_defecto(self):
        self.zona1_inicio.set("15:00")
        self.zona1_fin.set("20:30")
        self.zona2_inicio.set("15:00")
        self.zona2_fin.set("20:30")
        self.zona3_inicio.set("20:00")
        self.zona3_fin.set("20:30")
        self.dias_riego_z1.set("1")  
        self.dias_riego_z2.set("1")  
        self.dias_riego_z3.set("2")  
        self.humedad_minima_z1.set("30")
        self.humedad_maxima_z1.set("60")
        self.humedad_minima_z2.set("30")
        self.humedad_maxima_z2.set("60")
        self.humedad_minima_z3.set("30")
        self.humedad_maxima_z3.set("60")
        messagebox.showinfo("Éxito", "Configuración por defecto restaurada")
    
    def obtener_configuracion_dict(self):
        return {
            "i_hora_riego_z1": self.zona1_inicio.get(),
            "f_hora_riego_z1": self.zona1_fin.get(),
            "i_hora_riego_z2": self.zona2_inicio.get(),
            "f_hora_riego_z2": self.zona2_fin.get(),
            "i_hora_riego_z3": self.zona3_inicio.get(),
            "f_hora_riego_z3": self.zona3_fin.get(),
            "dias_riego_z1": int(self.dias_riego_z1.get()),
            "dias_riego_z2": int(self.dias_riego_z2.get()),
            "dias_riego_z3": int(self.dias_riego_z3.get()),
            "humedad_minima_z1": int(self.humedad_minima_z1.get()),
            "humedad_maxima_z1": int(self.humedad_maxima_z1.get()),
            "humedad_minima_z2": int(self.humedad_minima_z2.get()),
            "humedad_maxima_z2": int(self.humedad_maxima_z2.get()),
            "humedad_minima_z3": int(self.humedad_minima_z3.get()),
            "humedad_maxima_z3": int(self.humedad_maxima_z3.get())
        }

class ComunicacionArduino:
    def __init__(self):  
        self.arduino = None
        
    def conectar(self):
        try:
            self.arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            return True
        except Exception as e:
            return False

    def enviar_datos(self, datos_clima):
        try:
            hora_actual = datetime.now().strftime("%H:%M")
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            prob_lluvia = datos_clima["clima"]["probabilidad_lluvia"]
            
            config = datos_clima["configuracion_riego"]
            # "FECHA|HORA|PROB_LLUVIA|Z1_HORARIOS|Z2_HORARIOS|Z3_HORARIOS|DIAS_Z1|DIAS_Z2|DIAS_Z3|HUM_MIN_Z1|HUM_MAX_Z1|HUM_MIN_Z2|HUM_MAX_Z2|HUM_MIN_Z3|HUM_MAX_Z3"
            str = (f"{fecha_actual}|{hora_actual}|{prob_lluvia}|"
                       f"{config['i_hora_riego_z1']}-{config['f_hora_riego_z1']}|"
                       f"{config['i_hora_riego_z2']}-{config['f_hora_riego_z2']}|"
                       f"{config['i_hora_riego_z3']}-{config['f_hora_riego_z3']}|"
                       f"{config['dias_riego_z1']}|{config['dias_riego_z2']}|{config['dias_riego_z3']}|"
                       f"{config['humedad_minima_z1']}|{config['humedad_maxima_z1']}|"
                       f"{config['humedad_minima_z2']}|{config['humedad_maxima_z2']}|"
                       f"{config['humedad_minima_z3']}|{config['humedad_maxima_z3']}\n")
            
            time.sleep(0.1)
            while self.arduino.in_waiting > 0:
                self.arduino.read(self.arduino.in_waiting)
            
            self.arduino.write(str.encode('utf-8'))
            self.arduino.flush()
            
            time.sleep(1)
            self.leer_respuestas()
            return True
        except Exception as e:
            return False

    def leer_respuestas(self):
        respuestas = []
        start_time = time.time()
        
        while time.time() - start_time < 3:
            try:
                if self.arduino.in_waiting > 0:
                    linea = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                    if linea:
                        print(f"📥 Arduino: {linea}")
                        respuestas.append(linea)
                time.sleep(0.05)
            except Exception as e:
                break
        
        return respuestas

    def cerrar(self):
        if self.arduino:
            self.arduino.close()

if __name__ == "__main__":
    app = HydroSmart()
    app.ejecutar()