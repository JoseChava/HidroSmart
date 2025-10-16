
class ZonaRiego {
  private:
    int pinSensor;
    int humedadActual;

  public:
    ZonaRiego(int _pinSensor) {
      pinSensor = _pinSensor;
      humedadActual = 0;
    }

    void iniciar() {
      pinMode(pinSensor, INPUT);
    }

    int leerHumedad() {
      int valorSensor = analogRead(pinSensor);
      humedadActual = map(valorSensor, 0, 1023, 100, 0);
      humedadActual = constrain(humedadActual, 0, 100);
      return humedadActual;
    }

    int getHumedad() { return humedadActual; }
};

class SistemaRiego {
  private:
    ZonaRiego zona1;
    ZonaRiego zona2;
    ZonaRiego zona3;
    unsigned long lastHumedadCheck;
    const int INTERVALO_LECTURA = 5000;

  public:
    SistemaRiego():
      zona1(A0),
      zona2(A1),
      zona3(A2)
    {
      lastHumedadCheck = 0;
    }

    void iniciar() {
      Serial.begin(115200);
      zona1.iniciar();
      zona2.iniciar();
      zona3.iniciar();
      Serial.println("Sistema iniciado");
    }

    void actualizarHumedades() {
      zona1.leerHumedad();
      zona2.leerHumedad();
      zona3.leerHumedad();
    }

    void mostrarEstado() {
      Serial.print("Z1: "); Serial.print(zona1.getHumedad());
      Serial.print("% Z2: "); Serial.print(zona2.getHumedad());
      Serial.print("% Z3: "); Serial.print(zona3.getHumedad());
      Serial.println("%");
    }

    void loop() {
      if (millis() - lastHumedadCheck >= INTERVALO_LECTURA) {
        actualizarHumedades();
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