"""Converte imagem pra formato LCD 128x32 (4 paginas x 128 bytes).
Uso: python convert_img.py <arquivo> [limiar]
"""

import sys
import os
from PIL import Image

THRESHOLD = 160


def image_to_lcd_bytes(img_path, threshold=THRESHOLD):
    img = Image.open(img_path).convert("L")
    w, h = img.size
    ratio = 128 / w
    new_h = int(h * ratio)
    img = img.resize((128, new_h), Image.LANCZOS)
    if new_h > 32:
        top = (new_h - 32) // 2
        img = img.crop((0, top, 128, top + 32))
    elif new_h < 32:
        padded = Image.new("L", (128, 32), 255)
        top = (32 - new_h) // 2
        padded.paste(img, (0, top))
        img = padded

    fb = bytearray(512)
    for y in range(32):
        for x in range(128):
            px = img.getpixel((x, y))
            if px < threshold:
                page = y // 8
                bit = 1 << (y % 8)
                fb[page * 128 + x] |= bit
    return fb


def fb_to_python(fb, var_name="DIO_FRAME"):
    hex_str = fb.hex()
    lines = []
    for i in range(0, len(hex_str), 2048):
        chunk = hex_str[i:i + 2048]
        escaped = "".join(f"\\x{chunk[j:j+2]}" for j in range(0, len(chunk), 2))
        lines.append(f'    b"{escaped}"')
    joined = " +\n".join(lines)
    return f"{var_name} = (\n{joined}\n)"


def preview_ascii(fb):
    for page in range(4):
        for row in range(8):
            line = ""
            for col in range(128):
                bit = 1 << row
                if fb[page * 128 + col] & bit:
                    line += "#"
                else:
                    line += " "
            print(line)
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python convert_img.py <imagem> [limiar]")
        sys.exit(1)

    path = sys.argv[1]
    if len(sys.argv) > 2:
        threshold = int(sys.argv[2])
    else:
        threshold = THRESHOLD

    if not os.path.exists(path):
        print(f"Arquivo nao encontrado: {path}")
        sys.exit(1)

    print(f"Convertendo {path} (limiar={threshold})...")
    fb = image_to_lcd_bytes(path, threshold)

    name = os.path.splitext(os.path.basename(path))[0].upper() + "_FRAME"
    code = fb_to_python(fb, name)

    out_path = os.path.join(os.path.dirname(path), f"{name.lower()}.py")
    with open(out_path, "w") as f:
        f.write("# Auto-gerado por convert_img.py\n")
        f.write(f"# Fonte: {os.path.basename(path)}\n\n")
        f.write(code + "\n")

    raw = os.path.getsize(out_path)
    print(f"Escrito {out_path} ({raw} bytes)")
    print("\nPreview ASCII (girado 90deg):")
    preview_ascii(fb)
