# Birdnet-GO to Lilygo T5 4.7 inch S3 e-ink
Contains Arduino sketch and basic scripts to push [fugleramme](https://github.com/arnegiacomo/fugleramme) artwork to ESP32 based Lilygo T5 4.7 inch S3 ink display based on birdnet-go detected birds.
Inspired by:
https://fugleramme.arnegiacomo.dev/
https://github.com/arnegiacomo/fugleramme

[Accompanying blog post](https://portegi.es/blog/fugleramme-birdnet-on-eink-part1)

# Quick start
1. Install and configure [birdnet-go](https://github.com/tphakala/birdnet-go)
1. Clone [fugleramme](https://github.com/arnegiacomo/fugleramme) where you intend to run the glue webserver (just used for the artwork)
1. Run `birdnet_to_eink_server.py` as a Flask app: `flask --app ./birdnet_to_eink.py run`
1. Flash `arduino_birdnet_eink.ino` to the ESP32 of the Lilygo T5 e-ink display
  - Make sure to first create and fill in a `secrets.h` for things like the SSID and wifi password:
```
#define WIFI_SSID ""
#define WIFI_PW ""
#define SERVER_ADDR ""
```


# Components
- `convert_webp.py`: takes a given image and converts it to eink bit packed format.
  Can output a direct `.h` file to be used with the example Lilygo T5 render sketch
  ```bash
  python ./convert_webp.py ./fugleramme-main/assets/artwork/classic/birds/pica-pica-2.webp 960 540 pica-pica-2.h  --mode pad --rotate 90
  ```
- `render_binary_eink.py`: takes a `.h` file produced by the previous step
  and renders it to the system picture viewer (mainly for debugging)
  ```
  python ./render_bindary_eink.py pica-pica-2.h
  ```
- `birdnet_to_eink_server.py`:
  Basic flask server with a single endpoint, coupled has to be coupled to an existing `birdnet-go` server, yielding binary encoded versions for the Lilygo e-ink display
- `arduino_birdnet_eink.ino`:
  Sketch that fetches artwork every from seconds from the above server and paints it to the eink display

# References
- https://github.com/arnegiacomo/fugleramme
- https://lilygo.cc/products/t5-4-7-inch-e-paper-v2-3
- https://github.com/Xinyuan-LilyGO/LilyGo-EPD47
- https://github.com/tphakala/birdnet-go
- https://github.com/Xinyuan-LilyGO/LilyGo-EPD47/tree/esp32s3
- https://github.com/espressif/arduino-esp32/blob/master/libraries/WiFi/examples/WiFiClient/WiFiClient.ino