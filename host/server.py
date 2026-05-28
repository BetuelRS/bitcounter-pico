import http.server
import json
import threading
import serial
import serial.tools.list_ports
import time
import sys
import os
import re
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = {"counter": 0, "leds": [0] * 8, "connected": False, "error": ""}
LOCK = threading.Lock()
SER = None


def find_port():
    print("[serial] Procurando Pico...")
    try:
        ports = serial.tools.list_ports.comports()
        for p in ports:
            try:
                s = serial.Serial(p.device, 115200, timeout=0.3, dsrdtr=False)
                try:
                    s.setDTR(False)
                except Exception:
                    pass
                time.sleep(0.15)
                s.reset_input_buffer()
                s.write(b"PING\n")
                time.sleep(0.05)
                resp = s.read(100)
                s.close()
                if b"PONG" in resp:
                    print(f"[serial] Pico encontrado em {p.device}")
                    return p.device
            except Exception:
                pass
    except Exception:
        pass

    if sys.platform == "win32":
        candidates = [f"COM{i}" for i in range(1, 21)]
    else:
        candidates = [f"/dev/ttyACM{i}" for i in range(8)] + [
            f"/dev/ttyUSB{i}" for i in range(8)
        ]

    for p in candidates:
        try:
            s = serial.Serial(p, 115200, timeout=0.3, dsrdtr=False)
            try:
                s.setDTR(False)
            except Exception:
                pass
            time.sleep(0.15)
            s.reset_input_buffer()
            s.write(b"PING\n")
            time.sleep(0.05)
            resp = s.read(100)
            s.close()
            if b"PONG" in resp:
                print(f"[serial] Pico encontrado em {p}")
                return p
        except Exception:
            pass
    print("[serial] Pico nao encontrado. Verifique:")
    print("       1. Pico conectado via USB")
    print("       2. main.py atualizado no Pico (com suporte a comandos serial)")
    return None


def serial_worker():
    global SER, STATE
    port = None

    if len(sys.argv) > 1:
        port = sys.argv[1]

    if not port:
        port = find_port()

    if not port:
        with LOCK:
            STATE["error"] = "Pico nao encontrado"
            STATE["connected"] = False
        print("[serial] Aguardando reconexao (a cada 5s)...")
        while True:
            time.sleep(5)
            port = find_port()
            if port:
                break
        print(f"[serial] Pico reconectado em {port}")
        # Fall through to connect logic below

    try:
        SER = serial.Serial(port, 115200, timeout=0.05, dsrdtr=False)
        try:
            SER.setDTR(False)
        except Exception:
            pass
        time.sleep(0.15)
        SER.reset_input_buffer()
        SER.write(b"GET\n")

        with LOCK:
            STATE["connected"] = True
            STATE["error"] = ""

        while True:
            try:
                line = SER.readline()
            except Exception:
                break
            if not line:
                continue
            line = line.decode("utf-8", errors="ignore").strip()
            if line.startswith("STATE:"):
                parts = line.split(":")
                if len(parts) >= 3:
                    try:
                        c = int(parts[1])
                        ls = [int(x) for x in parts[2][:8]]
                        with LOCK:
                            STATE["counter"] = c
                            STATE["leds"] = ls
                    except ValueError:
                        pass
    except serial.SerialException as e:
        with LOCK:
            STATE["error"] = str(e)
    finally:
        with LOCK:
            STATE["connected"] = False
        if SER:
            try:
                SER.close()
            except Exception:
                pass
            SER = None


def send_cmd(cmd):
    if SER and SER.is_open:
        try:
            SER.write((cmd + "\n").encode())
            return True
        except Exception:
            return False
    return False


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = self.path.split("?", 1)
        path = parsed[0]
        qs = parsed[1] if len(parsed) > 1 else ""
        params = dict(re.findall(r"(\w+)=(-?\d+)", qs))

        if path == "/":
            self._serve_html()
        elif path == "/state":
            with LOCK:
                self._json(STATE)
        elif path == "/set":
            if "value" in params:
                v = max(0, min(255, int(params["value"])))
                ok = send_cmd(f"SET:{v}")
                time.sleep(0.05)
                self._json({"ok": ok}, 200 if ok else 503)
            else:
                self._json({"ok": False, "error": "missing value"}, 400)
        elif path == "/toggle":
            if "led" in params:
                idx = int(params["led"])
                if 0 <= idx < 8:
                    ok = send_cmd(f"TOGGLE:{idx}")
                    time.sleep(0.05)
                    self._json({"ok": ok}, 200 if ok else 503)
                else:
                    self._json({"ok": False, "error": "led out of range"}, 400)
            else:
                self._json({"ok": False, "error": "missing led"}, 400)
        elif path == "/inc":
            ok = send_cmd("INC")
            time.sleep(0.05)
            self._json({"ok": ok}, 200 if ok else 503)
        elif path == "/reset":
            ok = send_cmd("RESET")
            time.sleep(0.05)
            self._json({"ok": ok}, 200 if ok else 503)
        else:
            self.send_error(404)

    def _serve_html(self):
        html_path = os.path.join(BASE, "index.html")
        try:
            with open(html_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, fmt, *args):
        pass


def main():
    port = int(os.environ.get("PORT", 8000))

    t = threading.Thread(target=serial_worker, daemon=True)
    t.start()

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"BitCounter Pico GUI: {url}")
    print("Pressione Ctrl+C para parar o servidor.")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        server.shutdown()


if __name__ == "__main__":
    main()
