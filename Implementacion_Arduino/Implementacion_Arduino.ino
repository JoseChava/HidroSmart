class ZonaRiego {
  private:
    int pinBomba;
    int pinSensor;
    int humedadActual;
    bool bombaActiva;

  public:
    ZonaRiego(int _pinBomba, int _pinSensor) {
      pinBomba = _pinBomba;
      pinSensor = _pinSensor;
      humedadActual = 0;
      bombaActiva = false;
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

    void controlarBomba(int humedadMinima, String zona) {
      leerHumedad();
      
      if (humedadActual < humedadMinima && !bombaActiva) {
        digitalWrite(pinBomba, HIGH);
        bombaActiva = true;
        Serial.println("MOTOR " + zona + " ACTIVADO");
      }
      else if (humedadActual >= humedadMinima && bombaActiva) {
        digitalWrite(pinBomba, LOW);
        bombaActiva = false;
        Serial.println("MOTOR " + zona + " DETENIDO");
      }
    }

    int getHumedad() { return humedadActual; }
    bool getEstado() { return bombaActiva; }
};

class SistemaRiego {
  private:
    ZonaRiego zona1;
    ZonaRiego zona2;
    ZonaRiego zona3;
    int HUMEDAD_MINIMA;
    unsigned long lastHumedadCheck;
    const int INTERVALO_LECTURA = 5000;

  public:
    SistemaRiego():
      zona1(2, A0),
      zona2(3, A1),
      zona3(4, A2)
    {
      HUMEDAD_MINIMA = 30;
      lastHumedadCheck = 0;
    }

    void iniciar() {
      Serial.begin(115200);
      pinMode(13, OUTPUT);
      digitalWrite(13, LOW);
      zona1.iniciar();
      zona2.iniciar();
      zona3.iniciar();
      Serial.println("SISTEMA INICIADO");
    }

    void actualizarHumedades() {
      zona1.leerHumedad();
      zona2.leerHumedad();
      zona3.leerHumedad();
    }

    void mostrarEstado() {
      Serial.print("Z1:" + String(zona1.getHumedad()) + "% ");
      Serial.print("Z2:" + String(zona2.getHumedad()) + "% ");
      Serial.print("Z3:" + String(zona3.getHumedad()) + "% ");
      
      if (zona1.getEstado()) Serial.print("[M1-ON] ");
      if (zona2.getEstado()) Serial.print("[M2-ON] ");
      if (zona3.getEstado()) Serial.print("[M3-ON] ");
      Serial.println();
    }

    void evaluar() {
      zona1.controlarBomba(HUMEDAD_MINIMA, "Z1");
      zona2.controlarBomba(HUMEDAD_MINIMA, "Z2");
      zona3.controlarBomba(HUMEDAD_MINIMA, "Z3");

      digitalWrite(13, (zona1.getEstado() || zona2.getEstado() || zona3.getEstado()) ? HIGH : LOW);
    }

    void procesarComando(String comando) {
      if (comando == "ESTADO") {
        mostrarEstado();
      }
      else if (comando.startsWith("UMBRAL=")) {
        HUMEDAD_MINIMA = comando.substring(7).toInt();
        Serial.println("UMBRAL " + String(HUMEDAD_MINIMA));
      }
      else if (comando == "TEST") {
        digitalWrite(2, HIGH);
        delay(1000);
        digitalWrite(2, LOW);
        digitalWrite(3, HIGH);
        delay(1000);
        digitalWrite(3, LOW);
        digitalWrite(4, HIGH);
        delay(1000);
        digitalWrite(4, LOW);
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