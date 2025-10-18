import requests
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import serial
import json
import os

ARDUINO_PORT = 'COM3'
BAUD_RATE = 115200

class ComunicacionArduino:
    def __init__(self):  
        self.arduino = None
        
    def conectar(self):
        try:
            self.arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            print("Arduino CONECTADO")
            return True
        except Exception as e:
            print(f"Arduino DESCONECTADO: {e}")
            return False

    def enviar_datos(self, datos_clima):
        try:
            hora_actual = datetime.now().strftime("%H:%M")
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            prob_lluvia = datos_clima["lluvia"]
            
            # Formato: FECHA|HORA|PROB_LLUVIA|DESCRIPCION
            datos_str = f"{fecha_actual}|{hora_actual}|{prob_lluvia}|{datos_clima['desc']}\n"
            
            time.sleep(0.1)
            while self.arduino.in_waiting > 0:
                self.arduino.read(self.arduino.in_waiting)
            
            self.arduino.write(datos_str.encode('utf-8'))
            self.arduino.flush()
            
            time.sleep(1)
            self.leer_respuestas()
            return True
        except Exception as e:
            print(f" Error enviando datos a Arduino: {e}")
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
            print("🔌 Conexión Arduino cerrada")

class HydroSmartSimple:
    def __init__(self):
        self.api_key = "10ab96a1dec2098d86096f30091ee55f"
        self.root = tk.Tk()
        self.arduino_com = ComunicacionArduino()
        self.arduino_conectado = False
        
    def crear_ui(self):
        self.root.title("HydroSmart Simple")
        self.root.geometry("450x250")
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        titulo = ttk.Label(main_frame, text="HYDROSMART SIMPLE", 
                          font=("Arial", 14, "bold"))
        titulo.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        self.arduino_label = ttk.Label(main_frame, text="Arduino: DESCONECTADO", 
                                      font=("Arial", 10), foreground="red")
        self.arduino_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.temp_label = ttk.Label(main_frame, text="Temp: --.-°C", font=("Arial", 10))
        self.temp_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        self.hum_label = ttk.Label(main_frame, text="Humedad: --%", font=("Arial", 10))
        self.hum_label.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        self.lluvia_label = ttk.Label(main_frame, text="Lluvia: --%", font=("Arial", 10))
        self.lluvia_label.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        self.desc_label = ttk.Label(main_frame, text="Descripción: --", font=("Arial", 10))
        self.desc_label.grid(row=5, column=0, sticky=tk.W, pady=2)
        
        self.hora_label = ttk.Label(main_frame, text="Hora: --:--:--", font=("Arial", 9))
        self.hora_label.grid(row=6, column=0, sticky=tk.W, pady=2)
        
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=7, column=0, pady=10)
        
        ttk.Button(botones_frame, text="Actualizar", 
                  command=self.actualizar_ui).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(botones_frame, text="Conectar Arduino", 
                  command=self.conectar_arduino).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(botones_frame, text="Desconectar Arduino", 
                  command=self.desconectar_arduino).pack(side=tk.LEFT, padx=5)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
    def conectar_arduino(self):
        self.arduino_conectado = self.arduino_com.conectar()
        if self.arduino_conectado:
            self.arduino_label.config(text="Arduino: CONECTADO", foreground="green")
        else:
            self.arduino_label.config(text="Arduino: DESCONECTADO", foreground="red")
        
    def desconectar_arduino(self):
        self.arduino_com.cerrar()
        self.arduino_conectado = False
        self.arduino_label.config(text="Arduino: DESCONECTADO", foreground="red")
        print("🔌 Arduino desconectado manualmente")
        
    def actualizar_ui(self):
        clima = self.obtener_clima()
        
        if clima:
            hora_actual = datetime.now().strftime("%H:%M:%S")
            
            self.temp_label.config(text=f"Temp: {clima['temp']}°C")
            self.hum_label.config(text=f"Humedad: {clima['hum']}%")
            self.lluvia_label.config(text=f"Lluvia: {clima['lluvia']}%")
            self.desc_label.config(text=f"Descripción: {clima['desc']}")
            self.hora_label.config(text=f"Hora: {hora_actual}")
            
            print(f"[{hora_actual}] Temp: {clima['temp']}C | Hum: {clima['hum']}% | Lluvia: {clima['lluvia']}% | {clima['desc']}")
            
            if self.arduino_conectado:
                if not self.arduino_com.enviar_datos(clima):
                    print(" Falló el envío a Arduino")
                    self.arduino_conectado = False
                    self.arduino_label.config(text="Arduino: ERROR", foreground="orange")
        else:
            self.temp_label.config(text="Temp: Error")
            self.hum_label.config(text="Humedad: Error")
            self.lluvia_label.config(text="Lluvia: Error")
            self.desc_label.config(text="Descripción: Error")
            print("Error obteniendo clima")
        
    def obtener_clima(self):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat=9.859&lon=-83.913&appid={self.api_key}&units=metric&lang=es"
            response = requests.get(url, timeout=10)
            datos = response.json()
            
            prob_lluvia = 0
            if 'rain' in datos and '1h' in datos['rain']:
                prob_lluvia = min(100, datos['rain']['1h'] * 20)
            elif datos['weather'][0]['main'].lower() in ['rain', 'drizzle', 'thunderstorm']:
                prob_lluvia = 80
            
            return {
                "temp": round(datos["main"]["temp"], 1),
                "hum": datos["main"]["humidity"],
                "lluvia": round(prob_lluvia),
                "desc": datos['weather'][0]['description']
            }
        except Exception as e:
            print(f"Error clima: {e}")
            return None

    def ejecutar(self):
        print("HYDROSMART SIMPLE")
        print("=== INICIANDO COMUNICACIÓN ARDUINO ===")
        
        self.conectar_arduino()
        
        self.crear_ui()
        self.actualizar_ui()
        self.programar_actualizacion()
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Detenido por usuario")
        finally:
            self.arduino_com.cerrar()
            self.root.quit()

    def programar_actualizacion(self):
        self.actualizar_ui()
        self.root.after(30000, self.programar_actualizacion)  

if __name__ == "__main__":
    HydroSmartSimple().ejecutar()