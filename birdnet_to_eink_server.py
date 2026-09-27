import argparse
import io
import os
from pathlib import Path
import random
import sys
from flask import Flask, jsonify, send_file
import requests

from convert_webp import convert_webp_to_raw_buffer

app = Flask(__name__)

"""
Server sent events at:
https://github.com/tphakala/birdnet-go/wiki/BirdNET-Go-Guide#detection-stream-endpoint
URL: GET /api/v2/detections/stream
Authentication: None required (public endpoint)
Rate Limiting: 10 connections per minute per IP address

Curl example:
```
# Simple detection monitor using curl
curl -N -H "Accept: text/event-stream" \
     "http://localhost:8080/api/v2/detections/stream" | \
while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        # Extract JSON data
        json_data="${line#data: }"

        # Parse with jq if available
        if command -v jq &> /dev/null; then
            # Check if it's a detection event
            if echo "$json_data" | jq -e '.commonName' &> /dev/null; then
                species=$(echo "$json_data" | jq -r '.commonName')
                confidence=$(echo "$json_data" | jq -r '.confidence')
                time=$(echo "$json_data" | jq -r '.time')

                echo "🐦 $time: $species (${confidence})"

                # Example: Log to file
                echo "$time,$species,$confidence" >> detections.csv

                # Example: Send desktop notification (Linux)
                # notify-send "Bird Detected" "$species detected with ${confidence} confidence"
            fi
        else
            echo "Raw data: $json_data"
        fi
    fi
done
```
"""

# Configuration
BIRD_PICS_PATH = Path("fugleramme-main/assets/artwork/classic/birds")


# Converted buffer, in arduino eink buffer
# contains webp -> raw bytes buffer
# TODO now not used
LATEST_BIRD_BUFFER = io.BytesIO()


@app.route("/latest", methods=["GET"])
def latest_bird():
    """
    Returns the E-Ink binary buffer for the latest bird detection.
    Falls back to perch rn
    """
    # Query Birdnet-go for latest detection
    try:
        # birdnet has SSE, but is kinda annoying with flask
        # so we query /api/v2/detections
        # which returns a datetime sorted array:
        #
        #         {
        #   "data": [
        #     {
        #       "id": 1061,
        #       "date": "2026-09-25",
        #       "time": "13:14:13",
        #       "timestamp": "2026-09-25T13:14:13Z",
        #       "source": {
        #         "id": "",
        #         "type": "rtsp",
        #         "displayName": ""
        #       },
        #       "beginTime": "2026-09-25T13:14:09Z",
        #       "endTime": "2026-09-25T13:14:21Z",
        #       "speciesCode": "",
        #       "scientificName": "Coloeus monedula",
        #       "commonName": "Eurasian Jackdaw",
        #       "confidence": 0.31,
        #       "clipName": "coloeus_monedula_31p_20260925T131415Z.wav",
        #       "modelType": "bird",
        #       "verified": "unverified",
        #       "locked": false,
        #       "daysSinceFirstSeen": 6,
        #       "daysThisYear": 6,
        #       "daysThisSeason": 3,
        #       "currentSeason": "fall"
        #     },
        # Query Birdnet-go for the latest detection via the API
        response = requests.get(
            app.config["birdnet_go_host"] + "/api/v2/detections",
            timeout=10,
        )
        response.raise_for_status()
        detections = response.json().get("data", [])
        if not detections:
            return jsonify({"error": "No detections"}), 500

        # Sort by timestamp descending to get the most recent detection
        # or random from the last x
        latest_detections = sorted(detections, key=lambda x: x["timestamp"], reverse=True)[0:10]
        latest_detection = random.choice(latest_detections)
        
        # latest_detection = sorted(detections, key=lambda x: x["timestamp"], reverse=True)[0]

        # `latin_name` is like `Coloeus monedula`
        latin_name = latest_detection["scientificName"]
        confidence = latest_detection["confidence"]
        ts_str = latest_detection["timestamp"]
    except Exception as e:
        return jsonify({"error": f"Birdnet-go query failed: {str(e)}"}), 500


    # image file names are generally in two formats
    # <genus>-<species>.webp
    # <genus>-<species>-<number>.webp
    # like
    #  - anas-acuta.webp
    #  - anas-crecca-2.webp
    # Unsure if all species will be here, so need to safely fall back (say to a previous detection or the current memory buffer)
    latin_name_tmp = latin_name.replace(" ", "-").lower()
    search_pattern = f"{latin_name_tmp}*.webp"
    print(f"Looking for {search_pattern}")
    bird_potential = list(BIRD_PICS_PATH.glob(search_pattern))
    print(bird_potential)

    if bird_potential:
        chosen_image_path = random.choice(bird_potential)
        buffer = convert_webp_to_raw_buffer(
            chosen_image_path,
            960,
            540,
            "pad",
            "4bit",
            270
        )
    else:
        # Just fall back to a perch
        perches = BIRD_PICS_PATH.parent / "perches"
        perches_pics = list(perches.glob("*.webp"))
        perch_pic = random.choices(perches_pics)
        buffer = convert_webp_to_raw_buffer(
            perch_pic,
            960,
            540,
            "pad",
            "4bit",
            270
        )

    tmp_buffer = io.BytesIO(bytes(buffer))
    return send_file(
        tmp_buffer,
        as_attachment=True,
        download_name="bird.bin",
        mimetype="application/octet-stream",
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--birdnetgo", type=str, help="BirdnetGO host")
    args = parser.parse_args()

    birdnet_go_host = args.birdnetgo or os.getenv("BIRDNET_GO_HOST")
    if not birdnet_go_host:
        print("specificy birdnetgo host")
        sys.exit(-1)

    app.config["birdnet_go_host"] = birdnet_go_host

    app.run(host="0.0.0.0", port=5000, debug=False)