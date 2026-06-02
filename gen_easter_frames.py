"""PC-side: gera frames comprimidos em binary para o Pico.
Uso: python gen_easter_frames.py
Gera: easter_frames.bin (lido pelo easter_apple.py)
"""

import math
import os
import struct


def _set(fb, x, y):
    if 0 <= x < 128 and 0 <= y < 32:
        page = y // 8
        bit = 1 << (y % 8)
        fb[page * 128 + x] |= bit


def _circle(fb, cx, cy, r):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= r * r:
                _set(fb, x, y)


def _line(fb, x1, y1, x2, y2):
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    x, y = x1, y1
    while True:
        _set(fb, x, y)
        if x == x2 and y == y2:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def _rle_encode(fb):
    out = bytearray()
    i = 0
    while i < 512:
        count = 1
        while i + count < 512 and count < 255 and fb[i + count] == fb[i]:
            count += 1
        out.append(count)
        out.append(fb[i])
        i += count
    return out


def _girl_frame(t, cx=64):
    fb = bytearray(512)
    head_y = 6
    body_top = 12
    body_bot = 22
    sw = int(4 * math.sin(t * 2))
    _circle(fb, cx, head_y, 4)
    for by in range(body_top, body_bot):
        w = 3 + (by - body_top) // 3
        for bx in range(cx - w, cx + w + 1):
            _set(fb, bx, by)
    _line(fb, cx - 5, body_top + 1, cx - 7 + sw, body_top + 6)
    _line(fb, cx + 5, body_top + 1, cx + 7 - sw, body_top + 6)
    skirt_w = 7 + int(3 * math.sin(t * 1.5))
    for by in range(body_bot, 30):
        w = int(3 + ((by - body_bot) / 8) * skirt_w)
        for bx in range(cx - w, cx + w + 1):
            _set(fb, bx, by)
    ux = cx + int(12 * math.sin(t * 0.5))
    uy = head_y - 6
    for a in range(13):
        angle = a * math.pi / 12
        ux2 = cx + int(14 * math.cos(angle))
        uy2 = uy + int(8 * math.sin(angle))
        _set(fb, int(cx + (ux2 - cx) * 0.5), int(uy - (uy - uy2) * 0.5))
    _line(fb, ux, uy, ux, body_top + 4)
    return _rle_encode(fb)


def _circle_frame(t):
    fb = bytearray(512)
    cx = 64 + int(40 * math.sin(t * 0.5))
    cy = 16 + int(8 * math.sin(t * 0.7))
    r = 10 + int(6 * math.sin(t * 0.3))
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            dx, dy = x - cx, y - cy
            d = math.sqrt(dx * dx + dy * dy)
            if abs(d - r) < 2.5:
                _set(fb, x, y)
    return _rle_encode(fb)


def _silhouette_frame(t):
    fb = bytearray(512)
    phase = t * 0.4
    for y in range(32):
        page = y // 8
        bit = 1 << (y % 8)
        off = page * 128
        for x in range(128):
            v = math.sin(x * 0.08 + phase) * math.cos(y * 0.12 + phase * 0.5)
            v += math.sin(x * 0.15 + phase * 1.3) * 0.5
            if v > 0.15:
                fb[off + x] |= bit
    return _rle_encode(fb)


def _spiral_frame(t):
    fb = bytearray(512)
    cx, cy = 64, 16
    for i in range(60):
        a = t * 2 + i * 0.6
        r = 2 + i * 0.3
        x = int(cx + r * math.cos(a))
        y = int(cy + r * math.sin(a) * 0.6)
        _set(fb, x, y)
    return _rle_encode(fb)


def _marching_squares(t):
    fb = bytearray(512)
    for y in range(32):
        page = y // 8
        bit = 1 << (y % 8)
        off = page * 128
        for x in range(128):
            v = math.sin(x * 0.1 + t * 0.5) + math.sin(y * 0.15 + t * 0.3)
            v += math.sin((x + y) * 0.06 + t * 0.4)
            if v > 0.2:
                fb[off + x] |= bit
    return _rle_encode(fb)


def _particles(t):
    fb = bytearray(512)
    for i in range(40):
        px = int(64 + 50 * math.sin(t * 0.3 + i * 1.7))
        py = int(16 + 14 * math.sin(t * 0.5 + i * 2.3))
        for dy in range(-1, 2):
            yy = py + dy
            if 0 <= yy < 32:
                page = yy // 8
                bit = 1 << (yy % 8)
                xx = px
                if 0 <= xx < 128:
                    fb[page * 128 + xx] |= bit
    return _rle_encode(fb)


def _tunnel(t):
    fb = bytearray(512)
    cx, cy = 64, 16
    for y in range(32):
        page = y // 8
        bit = 1 << (y % 8)
        off = page * 128
        for x in range(128):
            dx = (x - cx) / 30
            dy = (y - cy) / 12
            d = math.sqrt(dx * dx + dy * dy)
            a = math.atan2(dy, dx)
            v = math.sin(d * 6 - t * 0.8) + math.sin(a * 5 + t * 0.4)
            if v > 0.3:
                fb[off + x] |= bit
    return _rle_encode(fb)


GENERATORS = [
    (_girl_frame, 60),
    (_circle_frame, 30),
    (_silhouette_frame, 30),
    (_spiral_frame, 25),
    (_marching_squares, 30),
    (_particles, 25),
    (_tunnel, 30),
    (_girl_frame, 60),
]


def generate():
    frames = []
    total = 0
    for gen, count in GENERATORS:
        for i in range(count):
            t = (i / count) * 6 * math.pi
            frames.append(gen(t))
            total += 1
            if total % 20 == 0:
                print(f"  Gerados {total} frames...")
    raw_total = sum(len(f) for f in frames)
    print(f"Total: {total} frames, {raw_total} bytes comprimidos")
    return frames


def write_binary(frames):
    path = os.path.join(os.path.dirname(__file__), "easter_frames.bin")
    with open(path, "wb") as f:
        f.write(struct.pack("<I", len(frames)))
        for rle in frames:
            f.write(struct.pack("<H", len(rle)))
            f.write(bytes(rle))
    size = os.path.getsize(path)
    print(f"Escrito {path} ({len(frames)} frames, {size} bytes)")


if __name__ == "__main__":
    print("Gerando frames...")
    frames = generate()
    write_binary(frames)
    print("Pronto!")
