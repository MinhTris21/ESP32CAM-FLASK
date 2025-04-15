#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>

const char* WIFI_SSID = "Suck my data";
const char* WIFI_PASS = "cykablyat";

WebServer server(80);

// Use only highest resolution
static auto hiRes = esp32cam::Resolution::find(1600, 1200);

void handleMjpegStream() {
  WiFiClient client = server.client();

  // MJPEG header
  server.sendContent("HTTP/1.1 200 OK\r\n");
  server.sendContent("Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n");

  while (client.connected()) {
    auto frame = esp32cam::capture();
    if (frame == nullptr) {
      Serial.println("Capture failed");
      continue;
    }

    String header = "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + String(frame->size()) + "\r\n\r\n";
    client.write((const uint8_t*)header.c_str(), header.length());
    frame->writeTo(client);
    client.write((const uint8_t*)"\r\n", 2);

    // Optional: small delay to reduce CPU load
    delay(50); // ~20 FPS max; increase to limit FPS
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println();

  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(hiRes);
    cfg.setBufferCount(2);   // Needed for high res
    cfg.setJpeg(90);         // High quality

    bool ok = Camera.begin(cfg);
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");
  }

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("Stream URL: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/cam.mjpeg");

  server.on("/cam.mjpeg", handleMjpegStream);
  server.begin();
}

void loop() {
  server.handleClient();
}
