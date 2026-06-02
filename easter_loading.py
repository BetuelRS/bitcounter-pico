import time


def _flush(lcd, fb):
    msg = bytearray(128)
    for page in range(4):
        lcd.WriteByte_command(0xb0 + page)
        lcd.WriteByte_command(0x10)
        lcd.WriteByte_command(0x00)
        off = page * 128
        msg[:] = fb[off:off + 128]
        lcd.i2c.writeto_mem(lcd.addr, 0x40, msg)


def play_loading(lcd, leds, pin_count, pin_reset):
    if not lcd:
        return

    fb = bytearray(512)

    for step in range(101):
        c_down = pin_count.value() == 0
        r_down = pin_reset.value() == 0
        if c_down or r_down:
            return

        for i in range(512):
            fb[i] = 0

        bar_w = step * 124 // 100
        for y in range(12, 20):
            page = y // 8
            bit = 1 << (y % 8)
            for x in range(2, 2 + bar_w):
                if 0 <= x < 128:
                    fb[page * 128 + x] |= bit

        for y in range(22, 30):
            page = y // 8
            bit = 1 << (y % 8)
            for x in range(2 + bar_w, 126):
                if 0 <= x < 128:
                    fb[page * 128 + x] |= bit

        _flush(lcd, fb)

        pat = 0
        for b in range(8):
            pat |= ((step + b * 3) % 10 < 5) << b
        for b in range(8):
            leds[b].value((pat >> b) & 1)

        time.sleep_ms(30)

        lcd.Clear()
        lcd.Cursor(0, 0)
        lcd.Display("CARREGANDO...")
        lcd.Cursor(1, 0)
        lcd.Display(f"  {step}%  ")
        lcd.Cursor(2, 0)
        lcd.Display("     ")
        lcd.Cursor(3, 0)
        lcd.Display("[                ]")

    for _ in range(20):
        c_down = pin_count.value() == 0
        r_down = pin_reset.value() == 0
        if c_down or r_down:
            return
        time.sleep_ms(10)

    lcd.Clear()
    lcd.Cursor(0, 0)
    lcd.Display("ERRO 404:")
    lcd.Cursor(1, 0)
    lcd.Display("AMIGO NAO")
    lcd.Cursor(2, 0)
    lcd.Display("ENCONTRADO!")
    lcd.Cursor(3, 0)
    lcd.Display(":(")

    for _ in range(100):
        for b in range(8):
            leds[b].value(1 if (_ + b) % 2 else 0)
        if pin_count.value() == 0 or pin_reset.value() == 0:
            break
        time.sleep_ms(100)

    for _ in range(5):
        for b in range(8):
            leds[b].value(1)
        time.sleep_ms(100)
        for b in range(8):
            leds[b].value(0)
        time.sleep_ms(100)
