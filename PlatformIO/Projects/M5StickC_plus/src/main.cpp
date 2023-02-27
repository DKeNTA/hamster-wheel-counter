//Low-level signal can be generated when the magnet S pole is close to the front of the sensor 
//OR the N pole is close to the back, and the internal LED indicator will light up, the screen wiil display 0.

#include <M5stickCPlus.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <time.h>
#include <stdio.h>
#define HALL_PIN 33

const char* ssid     = "BCW710J-D92CE-G";
const char* password = "544558d777de8";

const int capacity = JSON_OBJECT_SIZE(1);
StaticJsonDocument<capacity> json_request;
char buffer[255];

const char *host = "https://a9atl802u7.execute-api.ap-northeast-1.amazonaws.com/default/count_to_table";

void header(const char *string, uint16_t color)
{
  M5.Lcd.fillScreen(color);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Lcd.fillRect(0, 0, 320, 30, TFT_BLACK);
  M5.Lcd.setTextDatum(TC_DATUM);
  M5.Lcd.drawString(string, 100, 3, 4);     
}

void setup() {
  M5.begin(true, false, true);
  M5.Lcd.setRotation(3);
  M5.Lcd.setCursor(0, 0, 2);

  M5.Lcd.println("Start Serial");
  Serial.begin(9600);
  while (!Serial);
  delay(100);

  M5.Lcd.printf("Connecting to %s ", ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    M5.Lcd.print(".");
  }
  Serial.println("");
  M5.Lcd.println(" CONNECTED");

  configTime(9 * 3600, 0, "ntp.nict.jp"); // Set ntp time to local

  header("HALL Sensor", TFT_BLACK);
  pinMode(HALL_PIN, INPUT);
}

int flag_status = 1;
int count = 800;
int flag_post = 0;

void loop() {
  struct tm timeInfo;
  getLocalTime(&timeInfo);

  bool status = digitalRead(HALL_PIN);
  M5.Lcd.setTextSize(2);
  M5.Lcd.setCursor(40, 60, 2);
  if (flag_status - status == 1) {
    count++;
  }
  // M5.Lcd.fillScreen(BLACK);
  M5.Lcd.printf("%02d : %02d : %02d\r\n  Count : %04d\r\n", timeInfo.tm_hour, timeInfo.tm_min, timeInfo.tm_sec, count);  

  if ((timeInfo.tm_min == 59) && timeInfo.tm_sec == 59 && flag_post == 0) {

    json_request["counter"] = count;
    
    serializeJson(json_request, Serial);
    Serial.println("");

    serializeJson(json_request, buffer, sizeof(buffer));

    HTTPClient http;
    http.begin(host);
    http.addHeader("Content-Type", "application/json");
    int status_code = http.POST((uint8_t*)buffer, strlen(buffer));
    Serial.printf("status_code : %d\r\n", status_code);
    //M5.Lcd.printf("status_code : %d\r\n", status_code);
    if (status_code == 200) {
      Stream* resp = http.getStreamPtr();

      DynamicJsonDocument json_response(255);
      deserializeJson(json_response, *resp);

      serializeJson(json_response, Serial);
      Serial.println("");
    }
    http.end();
    count = 0;
    M5.Lcd.printf("");
    flag_post = 1;
  } else if (timeInfo.tm_sec == 1) {
    flag_post = 0;
  }
  flag_status = status;
}