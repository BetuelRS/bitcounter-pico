from machine import Pin
import time
import sys
import select

LED_PINS = [8, 9, 10, 11, 12, 13, 14, 15]
BTN_COUNT_PIN = 16
BTN_RESET_PIN = 17
DEBOUNCE_MS = 50

leds = [Pin(pin, Pin.OUT) for pin in LED_PINS]
btn_count = Pin(BTN_COUNT_PIN, Pin.IN, Pin.PULL_UP)
btn_reset = Pin(BTN_RESET_PIN, Pin.IN, Pin.PULL_UP)

counter = 0

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


show_binary(counter)
send_state()

while True:
    s = bcount.read()
    if s != prev_count and s == 0:
        counter = (counter + 1) % 256
        show_binary(counter)
        send_state()
    prev_count = s

    s = breset.read()
    if s != prev_reset and s == 0:
        counter = 0
        show_binary(counter)
        send_state()
    prev_reset = s

    if poll_obj.poll(0):
        try:
            line = sys.stdin.readline()
            if line:
                process_command(line.strip())
        except Exception:
            pass

    time.sleep_ms(5)
