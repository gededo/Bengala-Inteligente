// =============================
//NOME DOS INTEGRANTES DO GRUPO:

// Luan Sol Alves Neres
// Luis Felipe Costa Pedro
// Gabriel Alves Duarte
// Caio Fontes dos Santos Manhães
// Guilherme Monteiro de Oliveira
// Gabriel Rogato Ribeiro

// =============================
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// =============================
// CONFIGURAÇÕES DE HARDWARE
// =============================
const int buzzer = 4;
const int trigPin = 5;
const int echoPin = 18;
const int ultra = 14;

Adafruit_MPU6050 mpu;

float xPrev = 0, yPrev = 0, zPrev = 0;

// =============================
// LIMITES CALIBRADOS
// =============================
// Ruído ~0.00–0.05
// Fraca: 0.10 – 1.8
// Média: 1.8 – 4.5
// Forte: > 4.5
const float LIMITE_FRACA = 1.8;
const float LIMITE_MEDIA = 4.5;

// =============================
// CONFIG Wi-Fi AP (Offline)
// =============================
const char* ssid     = "BengalaWiFi";
const char* password = "12345678";

// =============================
// CONFIG MQTT
// =============================
WiFiClient espClient;
PubSubClient client(espClient);

// IMPORTANTE: IP do notebook quando conectado ao AP do ESP32
// normalmente 192.168.4.2
const char* mqtt_server = "192.168.4.2";

// Identificação da bengala/usuário
const char* user_id = "user01";
const char* cane_id = "caneA";

// =============================
// FUNÇÃO MQTT DE RECONEXÃO
// =============================
void reconnect() {
  while (!client.connected()) {
    Serial.print("Conectando ao MQTT...");
    if (client.connect("ESP32-Bengala")) {
      Serial.println("Conectado!");
      client.publish("bengala/debug", "ESP32 conectado.");
    } else {
      Serial.print("Falha, rc=");
      Serial.print(client.state());
      Serial.println(" - tentando de novo em 2s");
      delay(2000);
    }
  }
}

// =============================
// SETUP
// =============================
void setup() {
  Serial.begin(115200);

  pinMode(buzzer, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(ultra, OUTPUT);

  digitalWrite(ultra, HIGH);

  Wire.begin(21, 22);

  if (!mpu.begin()) {
    Serial.println("Erro ao iniciar MPU6050!");
    while (1);
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);

  // --------- Access Point ---------
  WiFi.softAP(ssid, password);
  delay(1000);

  Serial.print("AP criado! SSID=");
  Serial.println(ssid);
  Serial.print("IP do ESP32 (AP): ");
  Serial.println(WiFi.softAPIP());

  // --------- MQTT ---------
  client.setServer(mqtt_server, 1883);
}

// =============================
// LOOP PRINCIPAL
// =============================
void loop() {

  // Mantém MQTT conectado
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // -------------------------
  // ULTRASSÔNICO
  // -------------------------
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);
  int distance = duration * 0.034 / 2;

  Serial.print("Distancia: ");
  Serial.print(distance);
  Serial.println(" cm");

  if (distance <= 37 && distance > 0) {
    digitalWrite(buzzer, HIGH);
  } else {
    digitalWrite(buzzer, LOW);
  }

  // -------------------------
  // ACELERÔMETRO
  // -------------------------
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  float x = a.acceleration.x;
  float y = a.acceleration.y;
  float z = a.acceleration.z;

  float dx = fabs(x - xPrev);
  float dy = fabs(y - yPrev);
  float dz = fabs(z - zPrev);

  float maior = max(dx, max(dy, dz));

  Serial.print("ΔX=");
  Serial.print(dx, 2);
  Serial.print(" ΔY=");
  Serial.print(dy, 2);
  Serial.print(" ΔZ=");
  Serial.println(dz, 2);

  // -------------------------
  // CLASSIFICAÇÃO DA BATIDA
  // -------------------------
  String intensidade = "";

  if (maior > LIMITE_MEDIA) {          // > 4.5
    intensidade = "forte";
    Serial.println("VARIACAO FORTE DETECTADA!");
  } else if (maior > LIMITE_FRACA) {   // (1.8, 4.5]
    intensidade = "media";
    Serial.println("VARIACAO MEDIA DETECTADA!");
  } else if (maior > 0.10) {           // (0.10, 1.8]
    intensidade = "fraca";
    Serial.println("VARIACAO FRACA DETECTADA!");
  }

  // Se houve batida, publica no MQTT
  if (intensidade != "") {
    String topic = "bengala/";
    topic += user_id;
    topic += "/";
    topic += cane_id;
    topic += "/batidas";

    // JSON simples
    String json = "{";
    json += "\"user_id\":\"";      json += user_id;        json += "\",";
    json += "\"cane_id\":\"";      json += cane_id;        json += "\",";
    json += "\"intensidade\":\"";  json += intensidade;    json += "\",";
    json += "\"nivel\":";          json += String(maior, 2); json += ",";
    json += "\"distancia\":";      json += String(distance); json += ",";
    json += "\"ts_device\":";      json += String(millis());
    json += "}";

    client.publish(topic.c_str(), json.c_str());

    Serial.print("[MQTT] Publicado: ");
    Serial.println(json);

    delay(300); // debounce
  }

  xPrev = x;
  yPrev = y;
  zPrev = z;

  delay(50);
}
