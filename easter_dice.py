import time
import random


def _flush(lcd, fb):
    msg = bytearray(128)
    for page in range(4):
        lcd.WriteByte_command(0xb0 + page)
        lcd.WriteByte_command(0x10)
        lcd.WriteByte_command(0x00)
        off = page * 128
        msg[:] = fb[off:off + 128]
        lcd.i2c.writeto_mem(lcd.addr, 0x40, msg)


def _clear(fb):
    for i in range(512):
        fb[i] = 0


def _fill_rect(fb, x, y, w, h):
    for dy in range(h):
        yy = y + dy
        if yy < 0 or yy >= 32:
            continue
        page = yy // 8
        bit = 1 << (yy % 8)
        for dx in range(w):
            xx = x + dx
            if 0 <= xx < 128:
                fb[page * 128 + xx] |= bit


DICE_DOTS = {
    1: [(64, 16)],
    2: [(48, 10), (80, 22)],
    3: [(48, 10), (64, 16), (80, 22)],
    4: [(44, 10), (84, 10), (44, 22), (84, 22)],
    5: [(44, 10), (84, 10), (64, 16), (44, 22), (84, 22)],
    6: [(44, 10), (84, 10), (44, 16), (84, 16), (44, 22), (84, 22)],
}


def play_dice(lcd, leds, pin_count, pin_reset):
    if not lcd:
        return

    fb = bytearray(512)
    result = 0
    rolling = False
    roll_timer = 0
    release_count = 0

    while True:
        c_down = pin_count.value() == 0
        r_down = pin_reset.value() == 0

        if r_down:
            release_count += 1
            if release_count >= 4:
                return
        else:
            release_count = 0

        if c_down and not rolling:
            rolling = True
            roll_timer = time.ticks_ms()

        if c_down and rolling:
            now = time.ticks_ms()
            if time.ticks_diff(now, roll_timer) >= 60:
                result = random.randint(1, 6)
                roll_timer = now

        if not c_down and rolling:
            rolling = False

        _clear(fb)
        _fill_rect(fb, 40, 6, 48, 22)
        _fill_rect(fb, 42, 8, 44, 18)

        if not rolling and result:
            dots = DICE_DOTS[result]
            for dx, dy in dots:
                _fill_rect(fb, dx - 2, dy - 2, 4, 4)

            if result <= 8:
                for b in range(8):
                    leds[b].value(1 if b < result else 0)

            lcd.Cursor(0, 12)
            lcd.Display(f"{result}")
        else:
            for b in range(8):
                leds[b].value(1 if (time.ticks_ms() // 60 + b * 3) % 2 else 0)

        _flush(lcd, fb)
        time.sleep_ms(30)
