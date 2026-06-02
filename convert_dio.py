from PIL import Image

img = Image.open("dio.jpg").convert("L").resize((128, 135), Image.LANCZOS)
cropped = img.crop((0, 48, 128, 80))

fb = bytearray(512)
for y in range(32):
    for x in range(128):
        px = cropped.getpixel((x, y))
        if px < 160:
            page = y // 8
            bit = 1 << (y % 8)
            fb[page * 128 + x] |= bit

hex_str = fb.hex()
parts = []
for i in range(0, len(hex_str), 1024):
    chunk = hex_str[i:i + 1024]
    escaped = "".join("\\x" + chunk[j:j + 2] for j in range(0, len(chunk), 2))
    parts.append('b"' + escaped + '"')
joined = " +\n".join(parts)

with open("dio_frame.py", "w") as f:
    f.write("# Auto-gerado de dio.jpg\n")
    f.write("DIO_DATA = (\n")
    f.write(joined + "\n")
    f.write(")\n")

print(f"Gerado dio_frame.py ({len(fb)} bytes)")
print(f"Tamanho do arquivo: {len(hex_str)//2} bytes de dados")
