#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ======================
// CONFIGURAÇÃO DO AP
// ======================
const char* ap_ssid = "BengalaWiFi";
const char* ap_password = "12345678";

// ESP32 como Access Point gera esta rede:
// ESP32 IP -> 192.168.4.1 (padrão)
// PC IP    -> 192.168.4.2 (normalmente)

// ======================
// CONFIGURAÇÃO MQTT
// ======================

// IMPORTANTE: IP do PC conectado no AP do ESP32.
// Em geral será 192.168.4.2, mas você pode conferir com "ipconfig".
const char* mqtt_server = "192.168.4.2";
const int   mqtt_port   = 1883;

WiFiClient espClient;
PubSubClient mqttClient(espClient);

const char* userId = "user01";
const char* caneId = "caneA";

void setupAP() {
  Serial.println("Iniciando Access Point...");
  WiFi.softAP(ap_ssid, ap_password);

  IPAddress myIP = WiFi.softAPIP();
  Serial.print("AP iniciado. IP do ESP32: ");
  Serial.println(myIP); // deve ser 192.168.4.1
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Conectando ao broker MQTT...");

    String clientId = "ESP32-Bengala-";
    clientId += String((uint32_t)ESP.getEfuseMac(), HEX);

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("conectado!");
    } else {
      Serial.print("falhou, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" tentando novamente em 3s");
      delay(3000);
    }
  }
}

void publicarBatida(const char* intensidade, float nivel) {
  String topic = "bengala/";
  topic += userId;
  topic += "/";
  topic += caneId;
  topic += "/batidas";

  StaticJsonDocument<256> doc;
  doc["user_id"]     = userId;
  doc["cane_id"]     = caneId;
  doc["intensidade"] = intensidade; // "fraca" | "media" | "forte"
  doc["nivel"]       = nivel;       // 0.0 a 1.0 (para análise futura)
  doc["ts_device"]   = millis();

  char buffer[256];
  size_t n = serializeJson(doc, buffer);

  bool ok = mqttClient.publish(topic.c_str(), buffer, n);
  if (!ok) {
    Serial.println("Falha ao publicar batida via MQTT!");
  } else {
    Serial.print("Publicado: ");
    Serial.println(buffer);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  setupAP(); // cria a rede BengalaWiFi

  mqttClient.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  // ------------------------------------------------------------------
  // AQUI entra sua lógica de acelerômetro + detecção de batida.
  // Por enquanto, vou simular uma batida forte a cada 5 segundos.
  // ------------------------------------------------------------------
  static unsigned long last = 0;
  if (millis() - last > 5000) {
    last = millis();
    publicarBatida("forte", 0.8f);  // simulação
  }
}
