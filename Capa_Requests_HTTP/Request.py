import requests
import time
from datetime import datetime

class HydroSmartSimple:
    def __init__(self):
        self.api_key = "10ab96a1dec2098d86096f30091ee55f"
        
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
        
        try:
            while True:
                clima = self.obtener_clima()
                
                if clima:
                    hora = datetime.now().strftime("%H:%M:%S")
                    print(f"[{hora}] Temp: {clima['temp']}C | Hum: {clima['hum']}% | Lluvia: {clima['lluvia']}% | {clima['desc']}")
                else:
                    print("Error obteniendo clima")
                
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("Detenido")

if __name__ == "__main__":
    HydroSmartSimple().ejecutar()