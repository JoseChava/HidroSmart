import requests
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk

class HydroSmartSimple:
    def __init__(self):
        self.api_key = "10ab96a1dec2098d86096f30091ee55f"
        self.root = tk.Tk()
        
    def crear_ui(self):
        self.root.title("HydroSmart Simple")
        self.root.geometry("400x200")
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        titulo = ttk.Label(main_frame, text="HYDROSMART SIMPLE", 
                          font=("Arial", 14, "bold"))
        titulo.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        self.temp_label = ttk.Label(main_frame, text="Temp: --.-°C", font=("Arial", 10))
        self.temp_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.hum_label = ttk.Label(main_frame, text="Humedad: --%", font=("Arial", 10))
        self.hum_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.lluvia_label = ttk.Label(main_frame, text="Lluvia: --%", font=("Arial", 10))
        self.lluvia_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.desc_label = ttk.Label(main_frame, text="Descripción: --", font=("Arial", 10))
        self.desc_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.hora_label = ttk.Label(main_frame, text="Hora: --:--:--", font=("Arial", 9))
        self.hora_label.grid(row=5, column=0, sticky=tk.W, pady=5)
        
        ttk.Button(main_frame, text="Actualizar", 
                  command=self.actualizar_ui).grid(row=6, column=0, pady=10)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
    def actualizar_ui(self):
        """Actualiza la interfaz con los datos más recientes del clima"""
        clima = self.obtener_clima()
        
        if clima:
            hora_actual = datetime.now().strftime("%H:%M:%S")
            
            self.temp_label.config(text=f"Temp: {clima['temp']}°C")
            self.hum_label.config(text=f"Humedad: {clima['hum']}%")
            self.lluvia_label.config(text=f"Lluvia: {clima['lluvia']}%")
            self.desc_label.config(text=f"Descripción: {clima['desc']}")
            self.hora_label.config(text=f"Hora: {hora_actual}")
            
            print(f"[{hora_actual}] Temp: {clima['temp']}C | Hum: {clima['hum']}% | Lluvia: {clima['lluvia']}% | {clima['desc']}")
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
        
        self.crear_ui()
        
        self.actualizar_ui()
        
        self.programar_actualizacion()
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Detenido")
            self.root.quit()

    def programar_actualizacion(self):
        self.actualizar_ui()
        self.root.after(30000, self.programar_actualizacion)  

if __name__ == "__main__":
    HydroSmartSimple().ejecutar()