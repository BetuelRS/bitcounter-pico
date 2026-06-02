import time
import random


def _flush(lcd, fb):
    for page in range(4):
        lcd.WriteByte_command(0xb0 + page)
        lcd.WriteByte_command(0x10)
        lcd.WriteByte_command(0x00)
        off = page * 128
        msg = bytearray(fb[off:off + 128])
        lcd.i2c.writeto_mem(lcd.addr, 0x40, msg)


def _clear_fb(fb):
    for i in range(len(fb)):
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


def _read_pin_raw(pin):
    return pin.value()


def play_game(lcd, leds, pin_count, pin_reset):
    if not lcd:
        return

    fb = bytearray(512)

    PLAYER_SIZE = 3
    OBS_SIZE = 3
    BASE_SPEED = 400
    MIN_SPEED = 80
    HOLD_EXIT_MS = 1500

    while True:
        px = 62
        lives = 8
        score = 0
        speed = BASE_SPEED
        obstacles = []
        last_spawn = time.ticks_ms()
        last_move = time.ticks_ms()
        game_over = False
        move_cooldown = 120
        both_held = 0

        for i in range(8):
            leds[i].value(1)
        time.sleep_ms(200)

        while True:
            now = time.ticks_ms()
            c_down = _read_pin_raw(pin_count) == 0
            r_down = _read_pin_raw(pin_reset) == 0

            if c_down and r_down:
                if both_held == 0:
                    both_held = now
                elif time.ticks_diff(now, both_held) >= HOLD_EXIT_MS:
                    return
            else:
                both_held = 0

            if game_over:
                for i in range(8):
                    leds[i].value(0)

                _clear_fb(fb)
                _flush(lcd, fb)

                if lcd:
                    lcd.Clear()
                    lcd.Cursor(1, 1)
                    lcd.Display("GAME OVER")
                    lcd.Cursor(2, 0)
                    s = str(score)
                    lcd.Display("Score:" + s)

                for _ in range(300):
                    if _read_pin_raw(pin_count) == 0 or _read_pin_raw(pin_reset) == 0:
                        time.sleep_ms(200)
                        break
                    time.sleep_ms(10)
                else:
                    return
                break

            if c_down and time.ticks_diff(now, last_move) > move_cooldown:
                px = (px - 4) % 128
                last_move = now
            if r_down and time.ticks_diff(now, last_move) > move_cooldown:
                px = (px + 4) % 128
                last_move = now

            if time.ticks_diff(now, last_spawn) > speed:
                ox = random.randint(0, 125)
                obstacles.append([ox, -OBS_SIZE])
                last_spawn = now
                speed = max(MIN_SPEED, speed - 3)

            new_obs = []
            for obs in obstacles:
                obs[1] += 1
                if obs[1] < 32:
                    new_obs.append(obs)
            obstacles = new_obs

            for obs in obstacles:
                ox, oy = obs[0], obs[1]
                if (px < ox + OBS_SIZE and px + PLAYER_SIZE > ox and
                    28 < oy + OBS_SIZE and 28 + PLAYER_SIZE > oy):
                    lives -= 1
                    obstacles.remove(obs)
                    if lives <= 0:
                        game_over = True
                    for i in range(8):
                        leds[i].value(1 if i < lives else 0)
                    if lives > 0:
                        for _ in range(3):
                            for i in range(8):
                                leds[i].value(0)
                            time.sleep_ms(50)
                            for i in range(lives):
                                leds[i].value(1)
                            time.sleep_ms(50)
                    break

            score += 1

            _clear_fb(fb)
            _fill_rect(fb, px, 28, PLAYER_SIZE, PLAYER_SIZE)
            for obs in obstacles:
                _fill_rect(fb, obs[0], obs[1], OBS_SIZE, OBS_SIZE)

            for i in range(8):
                leds[i].value(1 if i < lives else 0)

            _flush(lcd, fb)
            time.sleep_ms(30)
