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


def _fill_cell(fb, gx, gy):
    x, y = gx * 4, gy * 4
    for dy in range(4):
        yy = y + dy
        page = yy // 8
        bit = 1 << (yy % 8)
        for dx in range(4):
            xx = x + dx
            if 0 <= xx < 128:
                fb[page * 128 + xx] |= bit


def play_snake(lcd, leds, pin_count, pin_reset):
    if not lcd:
        return

    fb = bytearray(512)
    COLS, ROWS = 32, 8
    cx, cy = COLS // 2, ROWS // 2
    snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
    dx, dy = 1, 0
    food = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
    while food in snake:
        food = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
    score = 0
    speed = 250
    both_held = 0

    while True:
        now = time.ticks_ms()
        c_down = pin_count.value() == 0
        r_down = pin_reset.value() == 0
        turned = False

        if c_down and r_down:
            if both_held == 0:
                both_held = now
            elif time.ticks_diff(now, both_held) >= 1500:
                return
        else:
            both_held = 0

        if c_down and not turned:
            dx, dy = -dy, dx
            turned = True
        if r_down and not turned:
            dx, dy = dy, -dx
            turned = True

        head = snake[0]
        nh = (head[0] + dx, head[1] + dy)

        if nh in snake or nh[0] < 0 or nh[0] >= COLS or nh[1] < 0 or nh[1] >= ROWS:
            _clear(fb)
            _flush(lcd, fb)
            lcd.Clear()
            lcd.Cursor(1, 4)
            lcd.Display("GAME OVER")
            lcd.Cursor(2, 2)
            lcd.Display(f"Score:{score}")
            for _ in range(200):
                if pin_count.value() == 0 or pin_reset.value() == 0:
                    time.sleep_ms(200)
                    return
                time.sleep_ms(10)
            return

        snake.insert(0, nh)
        if nh == food:
            score += 1
            speed = max(80, speed - 5)
            food = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            while food in snake:
                food = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        else:
            snake.pop()

        _clear(fb)
        for seg in snake:
            _fill_cell(fb, seg[0], seg[1])
        _fill_cell(fb, food[0], food[1])

        for b in range(8):
            leds[b].value(1 if b < min(score, 8) else 0)

        _flush(lcd, fb)
        time.sleep_ms(speed)
