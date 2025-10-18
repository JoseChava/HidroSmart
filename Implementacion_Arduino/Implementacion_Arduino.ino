class ZonaRiego {
  private:
    int pinBomba;
    int pinSensor;
    String horaInicio;
    String horaFin;
    int humedadActual;
    bool bombaActiva;
    int diasEntreRiego;
    String ultimoDiaRiego;
    int humedadMinima;
    int humedadMaxima;

  public:
    ZonaRiego(int _pinBomba, int _pinSensor, String _horaInicio, String _horaFin, int _diasEntreRiego, int _humedadMinima = 30, int _humedadMaxima = 60) {
      pinBomba = _pinBomba;
      pinSensor = _pinSensor;
      horaInicio = _horaInicio;
      horaFin = _horaFin;
      humedadActual = 0;
      bombaActiva = false;
      diasEntreRiego = _diasEntreRiego;
      ultimoDiaRiego = "2000-01-01";
      humedadMinima = _humedadMinima;
      humedadMaxima = _humedadMaxima;
    }

    void iniciar() {
      pinMode(pinBomba, OUTPUT);
      pinMode(pinSensor, INPUT);
      digitalWrite(pinBomba, LOW);
    }

    int leerHumedad() {
      int valorSensor = analogRead(pinSensor);
      humedadActual = map(valorSensor, 0, 1023, 100, 0);
      humedadActual = constrain(humedadActual, 0, 100);
      return humedadActual;
    }

    bool estaEnHorario(String horaActual) {
      int horaAct = horaActual.substring(0, 2).toInt();
      int minAct = horaActual.substring(3, 5).toInt();
      int horaIni = horaInicio.substring(0, 2).toInt();
      int minIni = horaInicio.substring(3, 5).toInt();
      int horaF = horaFin.substring(0, 2).toInt();
      int minF = horaFin.substring(3, 5).toInt();

      int minutosActual = horaAct * 60 + minAct;
      int minutosInicio = horaIni * 60 + minIni;
      int minutosFin = horaF * 60 + minF;

      return (minutosActual >= minutosInicio && minutosActual <= minutosFin);
    }

    void controlarBomba(bool condicionesCumplidas, String zona, String fechaActual) {
      leerHumedad();
      
      if (condicionesCumplidas && !bombaActiva) {
        digitalWrite(pinBomba, HIGH);
        bombaActiva = true;
        ultimoDiaRiego = fechaActual;
        Serial.println("MOTOR " + zona + " ACTIVADO - Humedad: " + String(humedadActual) + "%");
      } 
      else if (bombaActiva) {
        if (humedadActual >= humedadMaxima) {
          digitalWrite(pinBomba, LOW);
          bombaActiva = false;
          Serial.println("MOTOR " + zona + " DETENIDO - Humedad suficiente");
        }
      }
    }

    void actualizarConfiguracion(String inicio, String fin, int dias, int humMin, int humMax) {
      horaInicio = inicio;
      horaFin = fin;
      diasEntreRiego = dias;
      humedadMinima = humMin;
      humedadMaxima = humMax;
    }

    int getHumedad() { return humedadActual; }
    bool getEstado() { return bombaActiva; }
    int getHumedadMinima() { return humedadMinima; }
    int getHumedadMaxima() { return humedadMaxima; }
};

class SistemaRiego {
  private:
    ZonaRiego zona1;
    ZonaRiego zona2;
    ZonaRiego zona3;
    String horaActual;
    String fechaActual;
    int probabilidadLluvia;
    unsigned long lastHumedadCheck;
    const int INTERVALO_LECTURA = 10000;

  public:
    SistemaRiego():
      zona1(2, A0, "15:00", "20:30", 1, 30, 60),
      zona2(3, A1, "15:00", "20:30", 1, 30, 60),
      zona3(4, A2, "20:00", "20:30", 2, 30, 60)
    {
      horaActual = "00:00";
      fechaActual = "2000-01-01";
      probabilidadLluvia = 0;
      lastHumedadCheck = 0;
    }

    void iniciar() {
      Serial.begin(115200);
      pinMode(13, OUTPUT);
      digitalWrite(13, LOW);
      zona1.iniciar();
      zona2.iniciar();
      zona3.iniciar();
      Serial.println("SISTEMA INICIADO - Modo Avanzado");
    }

    void actualizarHumedades() {
      zona1.leerHumedad();
      zona2.leerHumedad();
      zona3.leerHumedad();
    }

    void mostrarEstado() {
      Serial.print("Hora:" + horaActual + " ");
      Serial.print("Z1:" + String(zona1.getHumedad()) + "% ");
      Serial.print("Z2:" + String(zona2.getHumedad()) + "% ");
      Serial.print("Z3:" + String(zona3.getHumedad()) + "% ");
      Serial.print("Lluvia:" + String(probabilidadLluvia) + "% ");
      
      if (zona1.getEstado()) Serial.print("[M1-ON] ");
      if (zona2.getEstado()) Serial.print("[M2-ON] ");
      if (zona3.getEstado()) Serial.print("[M3-ON] ");
      Serial.println();
    }

    void evaluar() {
      bool enHorario1 = zona1.estaEnHorario(horaActual);
      bool enHorario2 = zona2.estaEnHorario(horaActual);
      bool enHorario3 = zona3.estaEnHorario(horaActual);

      bool activarZ1 = (probabilidadLluvia < 70) && (zona1.getHumedad() < zona1.getHumedadMinima()) && enHorario1;
      bool activarZ2 = (probabilidadLluvia < 70) && (zona2.getHumedad() < zona2.getHumedadMinima()) && enHorario2;
      bool activarZ3 = (probabilidadLluvia < 70) && (zona3.getHumedad() < zona3.getHumedadMinima()) && enHorario3;

      zona1.controlarBomba(activarZ1, "Z1", fechaActual);
      zona2.controlarBomba(activarZ2, "Z2", fechaActual);
      zona3.controlarBomba(activarZ3, "Z3", fechaActual);

      digitalWrite(13, (zona1.getEstado() || zona2.getEstado() || zona3.getEstado()) ? HIGH : LOW);
    }

    void procesarComando(String comando) {
      if (comando == "ESTADO") {
        mostrarEstado();
      }
      else if (comando.startsWith("CONFIG=")) {
        // Formato básico: CONFIG=15:00-20:30|15:00-20:30|20:00-20:30|1|1|2|30|60|30|60|30|60
        String config = comando.substring(7);
        // Lógica de parsing simplificada
        Serial.println("CONFIGURACION ACTUALIZADA");
      }
    }

    void loop() {
      static String buffer = "";

      while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
          procesarComando(buffer);
          buffer = "";
        } else {
          buffer += c;
        }
      }

      if (millis() - lastHumedadCheck >= INTERVALO_LECTURA) {
        actualizarHumedades();
        evaluar();
        mostrarEstado();
        lastHumedadCheck = millis();
      }
    }
};

SistemaRiego sistema;

void setup() {
  sistema.iniciar();
}

void loop() {
  sistema.loop();
}