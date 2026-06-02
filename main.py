from machine import Pin
import time
import sys
import select

try:
    from lcd128_32 import lcd128_32
    import lcd128_32_fonts
    lcd = lcd128_32(20, 21, 0, 0x3f)
    lcd.Clear()
except Exception:
    lcd = None

try:
    from easter_game import play_game
except ImportError:
    play_game = None
try:
    from easter_pong import play_pong
except ImportError:
    play_pong = None
try:
    from easter_snake import play_snake
except ImportError:
    play_snake = None
try:
    from easter_loading import play_loading
except ImportError:
    play_loading = None
try:
    from easter_dice import play_dice
except ImportError:
    play_dice = None

LED_PINS = [8, 9, 10, 11, 12, 13, 14, 15]
BTN_COUNT_PIN = 16
BTN_RESET_PIN = 17
DEBOUNCE_MS = 50

leds = [Pin(pin, Pin.OUT) for pin in LED_PINS]
btn_count = Pin(BTN_COUNT_PIN, Pin.IN, Pin.PULL_UP)
btn_reset = Pin(BTN_RESET_PIN, Pin.IN, Pin.PULL_UP)

counter = 0
MODE_NORMAL = 0
MODE_GAME = 1
MODE_PONG = 2
MODE_SNAKE = 3
MODE_LOADING = 4
MODE_DICE = 5
mode = MODE_NORMAL
cg_hold = 0
pg_hold = 0
sn_hold = 0
ld_hold = 0
dc_hold = 0
HOLD_MS = 1500

poll_obj = select.poll()
poll_obj.register(sys.stdin, select.POLLIN)


class DebouncedButton:
    def __init__(self, pin):
        self.pin = pin
        self.last = 1
        self.stable = 1
        self.changed_at = time.ticks_ms()

    def read(self):
        now = time.ticks_ms()
        raw = self.pin.value()
        if raw != self.last:
            self.changed_at = now
        if raw != self.stable and time.ticks_diff(now, self.changed_at) >= DEBOUNCE_MS:
            self.stable = raw
        self.last = raw
        return self.stable == 0


bcount = DebouncedButton(btn_count)
breset = DebouncedButton(btn_reset)
prev_count = 1
prev_reset = 1

def show_binary(value):
    for i in range(8):
        leds[i].value((value >> i) & 1)


def send_state():
    bits = "".join(str(leds[i].value()) for i in range(8))
    print(f"STATE:{counter}:{bits}")
    if lcd:
        lcd.Clear()
        lcd.Cursor(0, 0)
        lcd.Display(f"Ct:{counter:3d}")
        lcd.Cursor(1, 0)
        lcd.Display(f"Bi:{bits}")
        lcd.Cursor(2, 0)
        lcd.Display(f"Hx:{counter:02X}")
        lcd.Cursor(3, 0)
        lcd.Display(f"GP:{counter:3d}")


def process_command(line):
    global counter
    if line.startswith("SET:"):
        try:
            val = int(line[4:])
            counter = max(0, min(255, val))
            show_binary(counter)
            send_state()
        except ValueError:
            pass
    elif line == "INC":
        counter = (counter + 1) % 256
        show_binary(counter)
        send_state()
    elif line == "RESET":
        counter = 0
        show_binary(counter)
        send_state()
    elif line.startswith("TOGGLE:"):
        try:
            idx = int(line[7:])
            if 0 <= idx < 8:
                leds[idx].value(1 - leds[idx].value())
                counter = sum(leds[i].value() << i for i in range(8))
                send_state()
        except ValueError:
            pass
    elif line == "GET":
        send_state()
    elif line == "PING":
        print("PONG")


def _reset_after_egg():
    global counter, mode, prev_count, prev_reset
    counter = 0
    show_binary(0)
    send_state()
    mode = MODE_NORMAL
    prev_count = bcount.read()
    prev_reset = breset.read()


show_binary(counter)
send_state()

while True:
    sc = bcount.read()
    if sc != prev_count and sc == 0:
        counter = (counter + 1) % 256
        show_binary(counter)
        send_state()
    prev_count = sc

    sr = breset.read()
    if sr != prev_reset and sr == 0:
        counter = 0
        show_binary(counter)
        send_state()
    prev_reset = sr

    if mode == MODE_NORMAL:
        if sc and not sr and counter == 13:
            if cg_hold == 0:
                cg_hold = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), cg_hold) >= HOLD_MS:
                if play_game:
                    mode = MODE_GAME
                    play_game(lcd, leds, btn_count, btn_reset)
                    _reset_after_egg()
                cg_hold = 0
        else:
            cg_hold = 0

        if sr and not sc and counter == 69:
            if pg_hold == 0:
                pg_hold = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), pg_hold) >= HOLD_MS:
                if play_pong:
                    mode = MODE_PONG
                    play_pong(lcd, leds, btn_count, btn_reset)
                    _reset_after_egg()
                pg_hold = 0
        else:
            pg_hold = 0

        if sr and not sc and counter == 99:
            if ld_hold == 0:
                ld_hold = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), ld_hold) >= HOLD_MS:
                if play_loading:
                    mode = MODE_LOADING
                    play_loading(lcd, leds, btn_count, btn_reset)
                    _reset_after_egg()
                ld_hold = 0
        else:
            ld_hold = 0

        if sc and sr and counter == 42:
            if sn_hold == 0:
                sn_hold = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), sn_hold) >= HOLD_MS:
                if play_snake:
                    mode = MODE_SNAKE
                    play_snake(lcd, leds, btn_count, btn_reset)
                    _reset_after_egg()
                sn_hold = 0
        else:
            sn_hold = 0

        if sc and sr and counter == 21:
            if dc_hold == 0:
                dc_hold = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), dc_hold) >= HOLD_MS:
                if play_dice:
                    mode = MODE_DICE
                    play_dice(lcd, leds, btn_count, btn_reset)
                    _reset_after_egg()
                dc_hold = 0
        else:
            dc_hold = 0

    if poll_obj.poll(0):
        try:
            line = sys.stdin.readline()
            if line:
                process_command(line.strip())
        except Exception:
            pass

    time.sleep_ms(5)
