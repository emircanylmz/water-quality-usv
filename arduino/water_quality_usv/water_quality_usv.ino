// Arduino firmware for the water-quality USV.
#include <OneWire.h>
#include <DallasTemperature.h>
#include <TinyGPS++.h>

// NEO-6M GPS: module TX -> Arduino Mega D19/RX1. D18/TX1 is not required.
const unsigned long GPS_BAUD = 9600;
const unsigned long GPS_FIX_MAX_AGE_MS = 5000;
TinyGPSPlus gps;

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
const unsigned long MEASUREMENT_INTERVAL_MS = 1000;
bool motorCommandActive = false;

void readGpsData() {
  while (Serial1.available() > 0) {
    gps.encode(Serial1.read());
  }
}

bool hasFreshGpsFix() {
  return gps.location.isValid() && gps.location.age() <= GPS_FIX_MAX_AGE_MS;
}

const char* classifyTurbidity(int rawValue) {
  return rawValue < turbidityThreshold ? "DIRTY" : "CLEAR";
}

void setup() {
  Serial.begin(9600);
  Serial1.begin(GPS_BAUD);

  pinMode(ENA, OUTPUT); pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);

  sensors.begin();
  // A blocking DS18B20 conversion can overflow the GPS UART buffer.
  sensors.setWaitForConversion(false);
  sensors.requestTemperatures();

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
  // NMEA verisini sürekli tüket; yalnız ölçüm anında okumak UART taşmasına yol açar.
  readGpsData();

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
  if (millis() - lastSendTime >= MEASUREMENT_INTERVAL_MS) {
    lastSendTime = millis();

    //pH Ölçümü
    for (int i = 0; i < 10; i++) {
      buf[i] = analogRead(pH_PIN);
      readGpsData();
      delay(5);
    }
    float avgValue = 0;
    for (int i = 0; i < 10; i++) avgValue += buf[i];
    float pHVol = (float)avgValue * 5.0 / 1024.0 / 10.0;
    float phValue = ph_formula(pHVol);

    //Turbidity Ölçümü
    int turbidityRaw = analogRead(TURBIDITY_PIN);
    const char* turbidityState = classifyTurbidity(turbidityRaw);

    //Sıcaklık Ölçümü
    float temperature = sensors.getTempCByIndex(0);
    sensors.requestTemperatures();

    readGpsData();

    // Yalnız geçerli ve güncel GPS fix'i olan ölçümler kayda gönderilir.
    if (!hasFreshGpsFix()) {
      Serial.println("GPS_NO_FIX");
      return;
    }

    // Raporda tanımlanan makine tarafından okunabilir telemetri paketi.
    Serial.print("LAT=");
    Serial.print(gps.location.lat(), 6);
    Serial.print(",LON=");
    Serial.print(gps.location.lng(), 6);
    Serial.print(",PH=");
    Serial.print(phValue, 2);
    Serial.print(",TURB=");
    Serial.print(turbidityRaw);
    Serial.print(",STATUS=");
    Serial.print(turbidityState);
    Serial.print(",TEMP=");
    Serial.println(temperature, 2);
  }
}
