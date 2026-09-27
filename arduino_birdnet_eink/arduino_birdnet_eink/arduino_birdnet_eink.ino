#ifndef BOARD_HAS_PSRAM
#error "Please enable PSRAM, Arduino IDE -> tools -> PSRAM -> OPI !!!"
#endif

/* 
 * Simple firmware that pulls already correctly encoded raw binary image data
 * from a server and paints it to the screen
 *
 * Write an image into a header file using a 3...2...1...0 format per pixel,
 * for 4 bits color (16 colors - well, greys.) MSB first.  At 80 MHz, screen
 * clears execute in 1.075 seconds and images are drawn in 1.531 seconds.
 * 
 * Based on:
 * - https://github.com/espressif/arduino-esp32/blob/master/libraries/WiFi/examples/WiFiClient/WiFiClient.ino
 * - https://github.com/Xinyuan-LilyGO/LilyGo-EPD47/blob/esp32s3/examples/drawImages/drawImages.ino
 * - https://arduino.stackexchange.com/questions/72052/how-to-get-the-body-of-an-http-request
 */

#include <Arduino.h>
#include "epd_driver.h"
#include "utilities.h"
#include "secrets.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <SPIFFS.h>
#include <TimeLib.h>
#include <AsyncDelay.h>

// Configuration
// Birdnet-go image converter server addr
const char* serverIP = SERVER_ADDR;
const int PORT = 5000;

// Device info
const char deviceid[] = "birdneteink";

// Wifi stuff
const char ssid[] = WIFI_SSID;
const char pass[] = WIFI_PW;

uint8_t *framebuffer;


// Times in ms
unsigned long WIFI_CONNECT_INTERVAL = 1000;
AsyncDelay wifi_delay;
WiFiClient client;

int image_width = 960;
int image_height = 520;

void setup()
{
  // Not entirely sure why/how but sometimes serial monitor never becomes active
  // even with USB CDC setup, this helps (?)
  Serial.begin(115200);
  while (!Serial) {
    delay(10); 
  }
  Serial.println("Starting\n");

  epd_init();

  // framebuffer size
  uint framebuffer_size = EPD_WIDTH * EPD_HEIGHT / 2;
  framebuffer = (uint8_t *)heap_caps_malloc(framebuffer_size, MALLOC_CAP_SPIRAM);
  Serial.println("Allocated");
  Serial.println(framebuffer_size);

  if (!framebuffer) {
      Serial.println("alloc memory failed !!!");
      while (1)
          ;
  }

  memset(framebuffer, 0xFF, EPD_WIDTH * EPD_HEIGHT / 2);


  wifi_delay.start(WIFI_CONNECT_INTERVAL, AsyncDelay::MILLIS);


  Serial.println("Connecting wifi");
  WiFi.mode(WIFI_STA);
  WiFi.hostname(deviceid);
  WiFi.begin(ssid, pass);
  Serial.println("Connected!");
}


void get_img_from_server() {
  Serial.println("Sending req");
  client.connect(serverIP, 5000);
  String req = "GET /latest HTTP/1.1";
  client.println(req);
  client.println("Host: birdneteink");
  client.println("Connection: close\r\n");
  client.print("\r\n");

  unsigned long timeout = millis();
  while (!client.available()) {
    if (millis() - timeout > 5000) {
      Serial.println("Timeout waiting for response");
      client.stop();
      return;
    }
  }
  // Parse the HTTP Headers
  // We look for the double CRLF (\r\n\r\n) which separates headers from the body
  bool headersFinished = false;
  unsigned long headerTimeout = millis();
  
  // We use a loop that continues as long as we haven't found the end 
  // OR we haven't hit a 5-second timeout.
  while (millis() - headerTimeout < 5000) {
    if (client.available()) {
      // Reset the timeout timer because we are actively receiving data
      headerTimeout = millis();

      // Read the next line until '\n'
      String line = client.readStringUntil('\n');
      
      // Print the line so you can see the headers in Serial Monitor
      Serial.print(line);
      Serial.println();

      if (line == "" || line == "\r") {
         Serial.println(); // Add a newline in Serial for readability
          headersFinished = true;
          break; 
      }
    }
    // Small delay to prevent slamming the CPU while waiting for network packets
    delay(1); 
  }

  if (headersFinished) {
    Serial.println("Headers found. Starting payload download...");

    // Fill the buffer
    int bytesReceived = 0;
    int maxBytes = 518400; 
    // allocated: 259200
    // TODO: check how the allocation math works, not sure
    while (client.available() && bytesReceived < maxBytes) {
      // Read one byte from the network
      uint8_t b = client.read();
      
      framebuffer[bytesReceived] = b;
      
      bytesReceived++;
      if (bytesReceived % 51200 == 0) {
        Serial.print("Progress: ");
        Serial.print(bytesReceived);
        Serial.println(" bytes");
      }
    }

    Serial.print("Download complete! Total bytes: ");
    Serial.println(bytesReceived);

  } else {
    Serial.println("Failed to find end of headers.");
  }

  Serial.println("Done.");
  client.stop();
}

void connect_wifi() {
    Serial.print("Checking wifi...");
    if (WiFi.status() == WL_CONNECTED) {
        Serial.print("\nconnecting...");
    }
}



void loop()
{
    Rect_t area = {
        .x = 0,
        .y = 0,
        .width = image_width,
        .height = image_height
    };
    epd_poweron();
    epd_clear();
    volatile uint32_t t1 = millis();
    epd_draw_grayscale_image(epd_full_screen(), framebuffer);
    volatile uint32_t t2 = millis();
    Serial.printf("EPD draw took %dms.\r\n", t2 - t1);
    epd_poweroff();
    delay(5000);
    Serial.println("Redraw!");
    get_img_from_server();

    if (wifi_delay.isExpired()) {
      if (!client.connected()) {
          connect_wifi();
      }
      wifi_delay.repeat();
    }
}