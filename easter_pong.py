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


def play_pong(lcd, leds, pin_count, pin_reset):
    if not lcd:
        return

    fb = bytearray(512)
    PW = 3
    PH = 8
    BW = 2
    L = 4
    R = 124
    ball_x, ball_y = 64, 16
    ball_dx = 1 if random.randint(0, 1) else -1
    ball_dy = 1 if random.randint(0, 1) else -1
    py1, py2 = 12, 12
    score1, score2 = 0, 0
    SPEED = 40
    both_held = 0

    while True:
        now = time.ticks_ms()
        c_down = pin_count.value() == 0
        r_down = pin_reset.value() == 0

        if c_down and r_down:
            if both_held == 0:
                both_held = now
            elif time.ticks_diff(now, both_held) >= 1500:
                return
        else:
            both_held = 0

        if c_down and py1 > 0:
            py1 -= 1
        if r_down and py1 < 24:
            py1 += 1

        target = ball_y - PH // 2
        diff = target - py2
        if abs(diff) > 1:
            py2 += 1 if diff > 0 else -1
        py2 = max(0, min(24, py2))

        ball_x += ball_dx
        ball_y += ball_dy

        if ball_y <= 0 or ball_y + BW >= 32:
            ball_dy *= -1

        if ball_x <= L + PW and py1 <= ball_y <= py1 + PH:
            ball_dx = 1
            ball_x = L + PW + 1
        if ball_x + BW >= R and py2 <= ball_y <= py2 + PH:
            ball_dx = -1
            ball_x = R - BW - 1

        if ball_x < 0:
            score2 += 1
            ball_x, ball_y = 64, 16
            ball_dx = 1
            ball_dy = 1 if random.randint(0, 1) else -1
            for i in range(3):
                leds[i].value(0)
                time.sleep_ms(80)
                leds[i].value(1)
                time.sleep_ms(80)
        if ball_x > 127:
            score1 += 1
            ball_x, ball_y = 64, 16
            ball_dx = -1
            ball_dy = 1 if random.randint(0, 1) else -1
            for i in range(3):
                leds[i].value(0)
                time.sleep_ms(80)
                leds[i].value(1)
                time.sleep_ms(80)

        _clear(fb)
        _fill_rect(fb, L, py1, PW, PH)
        _fill_rect(fb, R, py2, PW, PH)
        _fill_rect(fb, ball_x, ball_y, BW, BW)
        for i in range(0, 128, 8):
            _fill_rect(fb, 63, i, 1, 4)

        for b in range(8):
            leds[b].value(1 if b < min(score1, 8) else 0)

        if score1 >= 8 or score2 >= 8:
            _clear(fb)
            _flush(lcd, fb)
            lcd.Clear()
            lcd.Cursor(1, 2)
            w = "P1" if score1 >= 8 else "P2"
            lcd.Display(f"{w} VENCEU!")
            time.sleep_ms(2000)
            return

        _flush(lcd, fb)
        time.sleep_ms(SPEED)
