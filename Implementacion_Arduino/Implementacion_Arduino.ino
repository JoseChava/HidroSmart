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
    bool evaluandoRiego;
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
      evaluandoRiego = false;
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

    bool esDiaDeRiego(String fechaActual) {
      if (diasEntreRiego == -1) {
        return false;
      }
      
      if (diasEntreRiego == 0) {
        return true;
      }
      
      if (ultimoDiaRiego == "2000-01-01") {
        return true;
      }
      
      if (ultimoDiaRiego != fechaActual) {
        int anioActual = fechaActual.substring(0, 4).toInt();
        int mesActual = fechaActual.substring(5, 7).toInt();
        int diaActual = fechaActual.substring(8, 10).toInt();
        
        int anioUltimo = ultimoDiaRiego.substring(0, 4).toInt();
        int mesUltimo = ultimoDiaRiego.substring(5, 7).toInt();
        int diaUltimo = ultimoDiaRiego.substring(8, 10).toInt();
        
        long diasDesdeUltimoRiego = (anioActual - anioUltimo) * 365 + 
                                   (mesActual - mesUltimo) * 30 + 
                                   (diaActual - diaUltimo);
        
        bool puedeRegar = (diasDesdeUltimoRiego >= diasEntreRiego + 1);
        return puedeRegar;
      }
      
      return true;
    }

    void actualizarUltimoRiego(String fechaActual) {
      ultimoDiaRiego = fechaActual;
    }

    bool debeDetenerRiego(String horaActual) {
      if (humedadActual >= humedadMaxima) {
        return true;
      }
      
      if (!estaEnHorario(horaActual) && humedadActual >= humedadMinima) {
        return true;
      }
      
      return false;
    }

    void controlarBomba(bool condicionesCumplidas, String zona, String fechaActual, String horaActual) {
      if (evaluandoRiego) {
        return;
      }
      
      evaluandoRiego = true;
      
      if (condicionesCumplidas && !bombaActiva) {
        digitalWrite(pinBomba, HIGH);
        bombaActiva = true;
        actualizarUltimoRiego(fechaActual);
      } 
      else if (bombaActiva) {
        if (debeDetenerRiego(horaActual)) {
          digitalWrite(pinBomba, LOW);
          bombaActiva = false;
        }
      }
      else if (!bombaActiva && condicionesCumplidas) {
        digitalWrite(pinBomba, HIGH);
        bombaActiva = true;
        actualizarUltimoRiego(fechaActual);
      }
      
      evaluandoRiego = false;
    }

    void actualizarConfiguracion(String inicio, String fin, int dias, int humMin, int humMax) {
      horaInicio = inicio;
      horaFin = fin;
      diasEntreRiego = dias;
      humedadMinima = humMin;
      humedadMaxima = humMax;
    }

    String getFrecuenciaTexto(int diasConfig) {
      if (diasConfig == -1) return "NUNCA";
      if (diasConfig == 0) return "DIARIO";
      if (diasConfig == 1) return "CADA_2_DIAS";
      if (diasConfig == 2) return "CADA_3_DIAS";
      return "CADA_" + String(diasConfig + 1) + "_DIAS";
    }

    int getHumedad() { return humedadActual; }
    bool getEstado() { return bombaActiva; }
    String getHoraInicio() { return horaInicio; }
    String getHoraFin() { return horaFin; }
    int getDiasEntreRiego() { return diasEntreRiego; }
    String getUltimoRiego() { return ultimoDiaRiego; }
    int getHumedadMinima() { return humedadMinima; }
    int getHumedadMaxima() { return humedadMaxima; }
    String getFrecuencia() { return getFrecuenciaTexto(diasEntreRiego); }
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
    const int PROB_LLUVIA_MAXIMA = 70;
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
    }

    void actualizarHumedades() {
      zona1.leerHumedad();
      zona2.leerHumedad();
      zona3.leerHumedad();
    }

    void mostrarEstado() {
      Serial.print("Fecha: "); Serial.print(fechaActual);
      Serial.print(" Hora: "); Serial.print(horaActual);
      
      Serial.print(" | Z1:"); Serial.print(zona1.getHumedad());
      Serial.print("% ("); Serial.print(zona1.getFrecuencia());
      Serial.print("/<"); Serial.print(zona1.getHumedadMinima());
      Serial.print("%)");
      
      Serial.print(" | Z2:"); Serial.print(zona2.getHumedad());
      Serial.print("% ("); Serial.print(zona2.getFrecuencia());
      Serial.print("/<"); Serial.print(zona2.getHumedadMinima());
      Serial.print("%)");
      
      Serial.print(" | Z3:"); Serial.print(zona3.getHumedad());
      Serial.print("% ("); Serial.print(zona3.getFrecuencia());
      Serial.print("/<"); Serial.print(zona3.getHumedadMinima());
      Serial.print("%)");
      
      Serial.print(" | Lluvia: "); Serial.print(probabilidadLluvia);
      Serial.println("%");
      
      Serial.print("Bombas - Z1:"); Serial.print(zona1.getEstado() ? "ON" : "OFF");
      Serial.print(" Z2:"); Serial.print(zona2.getEstado() ? "ON" : "OFF");
      Serial.print(" Z3:"); Serial.println(zona3.getEstado() ? "ON" : "OFF");
    }

    bool condicionesParaActivar(int humedad, bool enHorario, bool esDiaRiego, String zona, int humedadMinima) {
      bool condicionesEmergencia = (probabilidadLluvia < PROB_LLUVIA_MAXIMA &&
                                   humedad < humedadMinima &&
                                   esDiaRiego);
      
      bool condicionesProgramadas = (probabilidadLluvia < PROB_LLUVIA_MAXIMA &&
                                    humedad < humedadMinima &&
                                    enHorario &&
                                    esDiaRiego);
      
      return condicionesEmergencia || condicionesProgramadas;
    }

    void evaluar() {
      bool enHorario1 = zona1.estaEnHorario(horaActual);
      bool enHorario2 = zona2.estaEnHorario(horaActual);
      bool enHorario3 = zona3.estaEnHorario(horaActual);
      
      bool diaRiego1 = zona1.esDiaDeRiego(fechaActual);
      bool diaRiego2 = zona2.esDiaDeRiego(fechaActual);
      bool diaRiego3 = zona3.esDiaDeRiego(fechaActual);

      bool activarZ1 = condicionesParaActivar(zona1.getHumedad(), enHorario1, diaRiego1, "Z1", zona1.getHumedadMinima());
      bool activarZ2 = condicionesParaActivar(zona2.getHumedad(), enHorario2, diaRiego2, "Z2", zona2.getHumedadMinima());
      bool activarZ3 = condicionesParaActivar(zona3.getHumedad(), enHorario3, diaRiego3, "Z3", zona3.getHumedadMinima());

      zona1.controlarBomba(activarZ1, "Z1", fechaActual, horaActual);
      zona2.controlarBomba(activarZ2, "Z2", fechaActual, horaActual);
      zona3.controlarBomba(activarZ3, "Z3", fechaActual, horaActual);

      digitalWrite(13, (zona1.getEstado() || zona2.getEstado() || zona3.getEstado()) ? HIGH : LOW);
    }

    void procesarDatos(String datos) {
      int pos1 = datos.indexOf('|');
      int pos2 = datos.indexOf('|', pos1 + 1);
      int pos3 = datos.indexOf('|', pos2 + 1);
      int pos4 = datos.indexOf('|', pos3 + 1);
      int pos5 = datos.indexOf('|', pos4 + 1);
      int pos6 = datos.indexOf('|', pos5 + 1);
      int pos7 = datos.indexOf('|', pos6 + 1);
      int pos8 = datos.indexOf('|', pos7 + 1);
      int pos9 = datos.indexOf('|', pos8 + 1);
      int pos10 = datos.indexOf('|', pos9 + 1);
      int pos11 = datos.indexOf('|', pos10 + 1);
      int pos12 = datos.indexOf('|', pos11 + 1);
      int pos13 = datos.indexOf('|', pos12 + 1);
      int pos14 = datos.indexOf('|', pos13 + 1);

      if (pos14 < 0) {
        Serial.println("Error de formato en datos recibidos");
        return;
      }

      fechaActual = datos.substring(0, pos1);
      horaActual = datos.substring(pos1 + 1, pos2);
      probabilidadLluvia = datos.substring(pos2 + 1, pos3).toInt();

      String z1 = datos.substring(pos3 + 1, pos4);
      String z2 = datos.substring(pos4 + 1, pos5);
      String z3 = datos.substring(pos5 + 1, pos6);
      
      int diasZ1 = datos.substring(pos6 + 1, pos7).toInt();
      int diasZ2 = datos.substring(pos7 + 1, pos8).toInt();
      int diasZ3 = datos.substring(pos8 + 1, pos9).toInt();
      
      int humMinZ1 = datos.substring(pos9 + 1, pos10).toInt();
      int humMaxZ1 = datos.substring(pos10 + 1, pos11).toInt();
      int humMinZ2 = datos.substring(pos11 + 1, pos12).toInt();
      int humMaxZ2 = datos.substring(pos12 + 1, pos13).toInt();
      int humMinZ3 = datos.substring(pos13 + 1, pos14).toInt();
      int humMaxZ3 = datos.substring(pos14 + 1).toInt();

      zona1.actualizarConfiguracion(z1.substring(0, z1.indexOf('-')), z1.substring(z1.indexOf('-') + 1), diasZ1, humMinZ1, humMaxZ1);
      zona2.actualizarConfiguracion(z2.substring(0, z2.indexOf('-')), z2.substring(z2.indexOf('-') + 1), diasZ2, humMinZ2, humMaxZ2);
      zona3.actualizarConfiguracion(z3.substring(0, z3.indexOf('-')), z3.substring(z3.indexOf('-') + 1), diasZ3, humMinZ3, humMaxZ3);

      actualizarHumedades();
      evaluar();
      mostrarEstado();
    }

    void loop() {
      static String buffer = "";

      while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
          if (buffer.length() > 10) {
            procesarDatos(buffer);
          }
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