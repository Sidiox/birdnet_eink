import re
import sys
from PIL import Image

def verify_header(header_file):
    with open(header_file, 'r') as f:
        content = f.read()

    # Parse dimensions using Regex
    width_match = re.search(r'image_width\s*=\s*(\d+);', content)
    height_match = re.search(r'image_height\s*=\s*(\d+);', content)

    if not width_match or not height_match:
        print("Error: Could not find image_width or image_height in header.")
        return

    width = int(width_match.group(1))
    height = int(height_match.group(1))
    total_pixels_expected = width * height

    # Parse the hex array
    # This looks for everything inside the { ... } of image_data
    array_match = re.search(r'image_data\[\]\s*=\s*\{([^}]*)\};', content, re.DOTALL)
    if not array_match:
        print("Error: Could not find image_data array.")
        return

    # Convert hex strings (0xAF) into a list of integers
    hex_strings = array_match.group(1).replace('\n', ' ').split(',')
    raw_data = []
    for s in hex_strings:
        clean_s = s.strip()
        if clean_s:
            raw_data.append(int(clean_s, 16))

    print(f"Found Header: {width}x{height}")
    print(f"Array contains {len(raw_data)} bytes.")

    # Determine Mode and Reconstruct Pixels
    pixels_8bit = []

    # Check if it's 4-bit (where 1 byte = 2 pixels) 
    # or 8-bit (where 1 byte = 1 pixel)
    if len(raw_data) == (total_pixels_expected // 2):
        print("Mode detected: 4-bit (Packed)")
        for byte in raw_data:
            # Extract High Nibble (p1) and Low Nibble (p2)
            p1 = (byte >> 4) & 0x0F
            p2 = byte & 0x0F
            
            # Scale 0-15 back up to 0-255 for display
            pixels_8bit.append((p1 * 255) // 15)
            pixels_8bit.append((p2 * 255) // 15)
    
    elif len(raw_data) == total_pixels_expected:
        print("Mode detected: 8-bit (Standard)")
        pixels_8bit = raw_data
    
    else:
        print(f"Error: Buffer size mismatch!")
        print(f"Expected {total_pixels_expected} pixels, but found {len(raw_data)} bytes.")
        print("If 4-bit, expected:", total_pixels_expected // 2)
        print("If 8-bit, expected:", total_pixels_expected)
        return

    # Create Image and Show
    if len(pixels_8bit) != total_pixels_expected:
        print(f"Warning: Reconstructed pixel count ({len(pixels_8bit)}) does not match dimensions ({total_pixels_expected})")

    img = Image.new('L', (width, height))
    img.putdata(pixels_8bit)
    
    print("Success! Opening image...")
    img.show()
    # Optional: save it
    # img.save("debug_output.png")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_header.py <your_file.h>")
        sys.exit(1)

    verify_header(sys.argv[1])