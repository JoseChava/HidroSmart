class ControlMotores {
  private:
    int relay1;
    int relay2;
    int relay3;
    bool estado1;
    bool estado2;
    bool estado3;

  public:
    ControlMotores(int r1, int r2, int r3) {
      relay1 = r1;
      relay2 = r2;
      relay3 = r3;
      estado1 = false;
      estado2 = false;
      estado3 = false;
    }

    void iniciar() {
      pinMode(relay1, OUTPUT);
      pinMode(relay2, OUTPUT);
      pinMode(relay3, OUTPUT);
      digitalWrite(relay1, LOW);
      digitalWrite(relay2, LOW);
      digitalWrite(relay3, LOW);
    }

    void activarMotor(int motor) {
      switch(motor) {
        case 1:
          digitalWrite(relay1, HIGH);
          estado1 = true;
          Serial.println("MOTOR 1 ON");
          break;
        case 2:
          digitalWrite(relay2, HIGH);
          estado2 = true;
          Serial.println("MOTOR 2 ON");
          break;
        case 3:
          digitalWrite(relay3, HIGH);
          estado3 = true;
          Serial.println("MOTOR 3 ON");
          break;
      }
    }

    void desactivarMotor(int motor) {
      switch(motor) {
        case 1:
          digitalWrite(relay1, LOW);
          estado1 = false;
          Serial.println("MOTOR 1 OFF");
          break;
        case 2:
          digitalWrite(relay2, LOW);
          estado2 = false;
          Serial.println("MOTOR 2 OFF");
          break;
        case 3:
          digitalWrite(relay3, LOW);
          estado3 = false;
          Serial.println("MOTOR 3 OFF");
          break;
      }
    }

    void toggleMotor(int motor) {
      switch(motor) {
        case 1:
          if(estado1) desactivarMotor(1);
          else activarMotor(1);
          break;
        case 2:
          if(estado2) desactivarMotor(2);
          else activarMotor(2);
          break;
        case 3:
          if(estado3) desactivarMotor(3);
          else activarMotor(3);
          break;
      }
    }

    void pruebaSecuencial() {
      Serial.println("INICIANDO PRUEBA SECUENCIAL");
      activarMotor(1);
      delay(2000);
      desactivarMotor(1);
      activarMotor(2);
      delay(2000);
      desactivarMotor(2);
      activarMotor(3);
      delay(2000);
      desactivarMotor(3);
      Serial.println("PRUEBA COMPLETADA");
    }

    void todosOn() {
      activarMotor(1);
      activarMotor(2);
      activarMotor(3);
    }

    void todosOff() {
      desactivarMotor(1);
      desactivarMotor(2);
      desactivarMotor(3);
    }

    void mostrarEstado() {
      Serial.print("M1:");
      Serial.print(estado1 ? "ON " : "OFF ");
      Serial.print("M2:");
      Serial.print(estado2 ? "ON " : "OFF ");
      Serial.print("M3:");
      Serial.println(estado3 ? "ON" : "OFF");
    }
};

ControlMotores motores(2, 3, 4);

void setup() {
  Serial.begin(9600);
  motores.iniciar();
  Serial.println("CONTROL DE MOTORES LISTO");
  Serial.println("COMANDOS: 1ON, 1OFF, 2ON, 2OFF, 3ON, 3OFF");
  Serial.println("TOGGLE: T1, T2, T3");
  Serial.println("GRUPOS: ALLON, ALLOFF, TEST, ESTADO");
}

void loop() {
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    
    if (comando == "1ON") motores.activarMotor(1);
    else if (comando == "1OFF") motores.desactivarMotor(1);
    else if (comando == "2ON") motores.activarMotor(2);
    else if (comando == "2OFF") motores.desactivarMotor(2);
    else if (comando == "3ON") motores.activarMotor(3);
    else if (comando == "3OFF") motores.desactivarMotor(3);
    else if (comando == "T1") motores.toggleMotor(1);
    else if (comando == "T2") motores.toggleMotor(2);
    else if (comando == "T3") motores.toggleMotor(3);
    else if (comando == "ALLON") motores.todosOn();
    else if (comando == "ALLOFF") motores.todosOff();
    else if (comando == "TEST") motores.pruebaSecuencial();
    else if (comando == "ESTADO") motores.mostrarEstado();
  }
}