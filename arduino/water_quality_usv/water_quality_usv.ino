// Arduino firmware for the water-quality USV.
#include <OneWire.h>
#include <DallasTemperature.h>

//pH Sensörü 
const int pH_PIN = A0;
int buf[10];

float ph_formula(float voltage) {
  return 7 + ((2.5 - voltage) / 0.18);  // Kalibrasyon formülü
}

//Turbidity Sensörü
const int TURBIDITY_PIN = A1;
const int turbidityThreshold = 500;

//Sıcaklık Sensörü
#define ONE_WIRE_BUS 1
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

//Motor Pinleri
#define ENA 9
#define ENB 3
#define IN1 7
#define IN2 6
#define IN3 5
#define IN4 4

const int slowPWM = 150; 
const int highPWM = 220; 
const int defaultPWM = 200;

unsigned long lastSendTime = 0;  // Zaman kontrolü
unsigned long lastCommandTime = 0;
const unsigned long COMMAND_TIMEOUT_MS = 2000;
bool motorCommandActive = false;

void setup() {
  Serial.begin(9600);

  pinMode(ENA, OUTPUT); pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);

  sensors.begin();

  motorA_stop();
  motorB_stop();
}

//Motor Fonksiyonları
void motorA_forward(){ digitalWrite(IN1,HIGH); digitalWrite(IN2,LOW); analogWrite(ENA, highPWM);}
void motorA_backward(){ digitalWrite(IN1,LOW); digitalWrite(IN2,HIGH); analogWrite(ENA, highPWM);}
void motorA_stop(){ analogWrite(ENA,0); }

void motorB_forward(){ digitalWrite(IN3,HIGH); digitalWrite(IN4,LOW); analogWrite(ENB, defaultPWM);}
void motorB_backward(){ digitalWrite(IN3,LOW); digitalWrite(IN4,HIGH); analogWrite(ENB, defaultPWM);}
void motorB_stop(){ analogWrite(ENB,0); }

void stopMotors(){
  motorA_stop();
  motorB_stop();
  motorCommandActive = false;
}

void handleMotorCommand(char cmd){
  switch(cmd) {
    case 'w': motorA_forward(); motorB_forward(); motorCommandActive = true; break;
    case 's': motorA_backward(); motorB_backward(); motorCommandActive = true; break;
    case 'd': motorB_forward(); motorA_stop(); motorCommandActive = true; break;
    case 'a': motorB_stop(); motorA_forward(); motorCommandActive = true; break;
    case 'x': stopMotors(); break;
    default:  stopMotors(); break;
  }
  lastCommandTime = millis();
}

void loop() {
  //Motor Komut Okuma
  while (Serial.available() > 0) {
    char cmd = Serial.read();
    handleMotorCommand(cmd);
  }

  // Haberleşme kesilirse son hareket komutunu sonsuza kadar sürdürme.
  if (motorCommandActive && millis() - lastCommandTime >= COMMAND_TIMEOUT_MS) {
    stopMotors();
  }

  // Veri Gönderme
  if (millis() - lastSendTime >= 1000) {
    lastSendTime = millis();

    //pH Ölçümü
    for (int i = 0; i < 10; i++) {
      buf[i] = analogRead(pH_PIN);
      delay(5);
    }
    float avgValue = 0;
    for (int i = 0; i < 10; i++) avgValue += buf[i];
    float pHVol = (float)avgValue * 5.0 / 1024.0 / 10.0;
    float phValue = -5.70 * pHVol + 21.34;  

    //Turbidity Ölçümü
    int turbidityRaw = analogRead(TURBIDITY_PIN);
    String turbidityState = (turbidityRaw < turbidityThreshold) ? "Kirli" : "Temiz";

    //Sıcaklık Ölçümü
    sensors.requestTemperatures();
    float temperature = sensors.getTempCByIndex(0);

    //Seri Gönderim Raspberry Pi'ye
    Serial.print("PH:");
    Serial.print(ph_formula(pHVol), 2);
    Serial.print(",CAL:");
    Serial.print(phValue, 2);
    Serial.print(",TURB:");
    Serial.print(turbidityState);
    Serial.print(",TEMP:");
    Serial.println(temperature, 2);

    Serial.print("pH: "); Serial.print(ph_formula(pHVol),2);
    Serial.print(" | Cal: "); Serial.print(phValue,2);
    Serial.print(" | Su Durumu: "); Serial.print(turbidityState);
    Serial.print(" | Sicaklik: "); Serial.println(temperature,2);
  }
}
