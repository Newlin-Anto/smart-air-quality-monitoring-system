#include <WiFi.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11

#define MQ7_PIN 34
#define MQ135_PIN 35
#define DUST_PIN 32
#define BUZZER_PIN 5   // NEW

const char* ssid = "world";
const char* password = "123456789";

String apiKey = "MTHPG94RR4IG6B5H";
const char* server = "api.thingspeak.com";

DHT dht(DHTPIN, DHTTYPE);
WiFiClient client;

// 🔴 Threshold (adjust after testing)
int MQ135_THRESHOLD = 1200;

void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("Connected!");
}

void loop() {

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  int mq7 = analogRead(MQ7_PIN);
  int mq135 = analogRead(MQ135_PIN);
  int dust = analogRead(DUST_PIN);

  int alertStatus = 0;  // NEW

  Serial.println("----Sensor Data----");
  Serial.println(temp);
  Serial.println(hum);
  Serial.println(mq7);
  Serial.println(mq135);
  Serial.println(dust);

  // 🚨 ALERT LOGIC
  if (mq135 > MQ135_THRESHOLD) {
    Serial.println("⚠️ AIR POLLUTION HIGH!");

    alertStatus = 1;

    // Buzzer ON pattern
    digitalWrite(BUZZER_PIN, HIGH);
    delay(500);
    digitalWrite(BUZZER_PIN, LOW);
    delay(200);
    digitalWrite(BUZZER_PIN, HIGH);
    delay(500);
    digitalWrite(BUZZER_PIN, LOW);

  } else {
    digitalWrite(BUZZER_PIN, LOW);
    alertStatus = 0;
  }

  // 🌐 ThingSpeak Upload (added field6)
  if (client.connect(server, 80)) {
    String url = "/update?api_key=" + apiKey +
                 "&field1=" + String(temp) +
                 "&field2=" + String(hum) +
                 "&field3=" + String(mq7) +
                 "&field4=" + String(mq135) +
                 "&field5=" + String(dust) +
                 "&field6=" + String(alertStatus);  // NEW FIELD

    client.print(String("GET ") + url + " HTTP/1.1\r\n" +
                 "Host: api.thingspeak.com\r\n" +
                 "Connection: close\r\n\r\n");
  }

  client.stop();

  delay(20000); // 2 sec
}
