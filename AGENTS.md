# BitCounter Pico

MicroPython binary counter for Raspberry Pi Pico with PC-based web GUI.

## Hardware

- 8 LEDs on GPIO 8–15 (active high, LSB = GPIO 8)
- Count button GPIO 16 (pull-up, active low)
- Reset button GPIO 17 (pull-up, active low)
- Button debounce: 50ms (`DebouncedButton` class, non-blocking)

## Architecture

```
Pico (MicroPython)         PC (Python + browser)
main.py  ←USB/serial→  host/server.py ←HTTP→ host/index.html
```

- `main.py` — sole Pico entrypoint (`machine`, `time`, `sys`, `select`). Polls buttons, processes serial commands, drives LEDs. CircuitPython NOT used — MicroPython only (`from machine import Pin`).
- `host/server.py` — PC entrypoint. Auto-detects Pico via `PING`/`PONG` probe, bridges serial ↔ HTTP. Depends on `pyserial`. Listens on `127.0.0.1` only (`PORT` env var, default 8000).
- `host/index.html` — static GUI served by server, polls `/state` every 120ms.

## Serial protocol (USB CDC, 115200 baud)

**Pico → PC** via `print`:
- `STATE:<counter>:<8-led-bits>` — on every state change

**PC → Pico** via `sys.stdin` (non-blocking, `select.poll(0)`):
- `SET:<value>` — set counter 0–255 (clamped)
- `TOGGLE:<led>` — toggle LED 0–7
- `INC` — increment counter (mod 256)
- `RESET` — reset to 0
- `GET` — request current state
- `PING` — health check; Pico replies `PONG`

## Commands

```bash
# Deploy to Pico
mpremote cp main.py :
mpremote reset

# Run host (PC)
pip install pyserial
python host/server.py              # auto-detect serial port
python host/server.py COM5         # or specify port explicitly
```

## Gotchas

- **Edge detection**: `DebouncedButton` tracks `prev` value, fires on falling edge (`s != prev and s == 0`). Follow this pattern when adding buttons.
- **Counter**: wraps via `(counter + 1) % 256` (modulo, not clamped to 255). `send_state()` reads LED pin values, not the counter variable directly — they are kept in sync.
- **Serial quirk**: `SER.setDTR(False)` called after opening the port — required for some RP2040 boards to avoid reset-on-connect.
- **No tests, linters, CI, package manager, or build system.** Git not initialized. `pyserial` is the only PC-side dependency.
