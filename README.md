# Birdnet-GO to Lilygo T5 4.7 inch S3 e-ink
Contains the arduino script to paint pictures of the birds detected by birdnet-go.

Inspired by 
https://fugleramme.arnegiacomo.dev/
https://github.com/arnegiacomo/fugleramme

# Components
- convert_webp.py: takes a given image and converts it to eink bit packed format.
  Can output a direct `.h` file to be used with the example Lilygo T5 render sketch
  ```bash
  python .\convert_webp.py .\fugleramme-main\assets\artwork\classic\birds\pica-pica-2.webp 960 540 pica-pica-2.h  --mode pad --rotate 90
  ```
- render_binary_eink.py: takes a `.h` file produced by the previous step
  and renders it to the system picture viewer (mainly for debugging)



# References
- https://github.com/Xinyuan-LilyGO/LilyGo-EPD47/tree/esp32s3
- https://github.com/espressif/arduino-esp32/blob/master/libraries/WiFi/examples/WiFiClient/WiFiClient.ino