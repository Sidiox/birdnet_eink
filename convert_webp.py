import argparse
from PIL import Image, ImageOps

def convert_webp_to_raw_buffer(
                           input_path,
                           width,
                           height,
                           mode,
                           bits,
                           rotate,
                           ):
    img = Image.open(input_path)
    print(f"  [Info] Original Size: {img.width}x{img.height} | Mode: {img.mode}")

    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        # Create a solid white background of the same size
        # We use RGBA for the background to allow alpha compositing
        background = Image.new('RGBA', img.size, (255, 255, 255, 255))
        
        # If it's a Palette image ('P'), convert to RGBA to handle transparency correctly
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Composite the image onto the white background
        img = Image.alpha_composite(background, img)
        print(f"  [Info] Transparency detected. Flattened onto white background.")
    
    # Now safely convert to Grayscale ('L')
    img = img.convert('L')
    print(f"  [Info] Original Size: {img.width}x{img.height}")

    # Manual or Auto Rotation
    if rotate != 'auto':
        rot_map = {'0': 0, '90': 90, '180': 180, '270': 270}
        angle = rot_map.get(rotate, 0)
        img = img.rotate(angle, expand=True)
        print(f"  [Info] Forced rotation: {angle} degrees")
    else:
        # Auto-detect: If taller than wide, rotate 90
        if img.height > img.width:
            img = img.transpose(Image.ROTATE_90)
            print(f"  [Info] Auto-rotated portrait to landscape.")

    # Scaling Modes
    if mode == 'fit':
        # CROP: Fills screen, cuts off edges
        img = ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
        print(f"  [Mode] Using 'fit' (Crop-to-fill): Edges will be cut to avoid stretching.")
    
    elif mode == 'pad':
        # PAD: Shows whole image, adds White bars (Letterboxing)
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        new_img = Image.new('L', (width, height), 255) # White background
        # Paste image in center
        offset = ((width - img.width) // 2, (height - img.height) // 2)
        new_img.paste(img, offset)
        img = new_img
        print(f"  [Mode] Using 'pad' (Letterbox): Whole image visible, White bars added.")
    
    elif mode == 'stretch':
        # STRETCH: Fills screen, no cutting, but distorts
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        print(f"  [Mode] Using 'stretch': Whole image visible, but may look distorted.")

    # 4. Quantize & Pack
    pixels = list(img.getdata())
    quantized = [(p * 15) // 255 for p in pixels]
    
    packed_data = []
    if bits == '4bit':
        for i in range(0, len(quantized), 2):
            p1 = quantized[i]
            p2 = quantized[i+1] if (i + 1) < len(quantized) else 0
            packed_data.append((p1 << 4) | p2)
    else:
        # 8-bit mode
        img_8bit = img.resize((width, height), Image.Resampling.LANCZOS)
        packed_data = list(img_8bit.getdata())

    return packed_data


def write_buffer_to_arduino_h(output_path, buffer, mode, bits, width, height):
    with open(output_path, 'w') as f:
        f.write(f"/* Generated for LilyGo T5 | Mode: {mode} | Bits: {bits} */\n")
        f.write(f"const unsigned int image_width = {width};\n")
        f.write(f"const unsigned int image_height = {height};\n\n")
        f.write(f"const unsigned char image_data[] = {{\n    ")
        for idx, val in enumerate(buffer):
            f.write(f"0x{val:02X}, ")
            if (idx + 1) % 12 == 0: f.write("\n    ")
        f.write("\n};\n")
        f.write(f"const unsigned int image_len = {len(buffer)};\n")

    print(f"Successfully saved to {output_path}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced WebP to E-Ink Header Converter")
    parser.add_argument("input", help="Input .webp file")
    parser.add_argument("width", type=int, help="Target Width")
    parser.add_argument("height", type=int, help="Target Height")
    parser.add_argument("output", help="Output .h file")
    parser.add_argument("--mode", choices=['fit', 'pad', 'stretch'], default='fit', help="Scaling mode: fit (crop), pad (letterbox), stretch (distort)")
    parser.add_argument("--bits", choices=['4bit', '8bit'], default='4bit', help="Bit depth")
    parser.add_argument("--rotate", choices=['auto', '0', '90', '180', '270'], default='auto', help="Manual rotation")

    args = parser.parse_args()
    result_buffer = convert_webp_to_raw_buffer(
        args.input,
        args.width,
        args.height,
        args.mode,
        args.bits,
        args.rotate,
    )

    write_buffer_to_arduino_h(
        args.output,
        result_buffer,
        args.mode,
        args.bits,
        args.width,
        args.height,
    )