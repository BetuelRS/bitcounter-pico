# BitCounter Pico ⚡

Contador binário de 8 bits com Raspberry Pi Pico, controle físico via botões e interface web no PC.

![Badge: MicroPython](https://img.shields.io/badge/MicroPython-3.x-2B2B2B?logo=micropython) ![Badge: Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python)

---

## Visão geral

O **BitCounter Pico** é um projeto educacional que ensina sistema binário na prática. Um Raspberry Pi Pico controla 8 LEDs representando bits (LSB → GPIO 8, MSB → GPIO 15). Um botão de incremento e um de reset permitem navegar pelos valores de 0 a 255 sem precisar do computador. Conectado via USB, uma interface web (servida pelo próprio PC) exibe o valor em tempo real, permite controle remoto e explica conceitos de binário.

---

## Hardware necessário

| Componente | Especificação | Qtd |
|---|---|---|
| Raspberry Pi Pico (RP2040) | Qualquer versão | 1 |
| LED difuso 5 mm | Vermelho, Azul, Amarelo, Verde | 8 |
| Resistor 330 Ω | 1/4 W | 8 |
| Push button (tátil) | 6×6 mm | 2 |
| Resistor 10 kΩ | pull-up externo (opcional — PULL_UP interno já usado) | 2 |
| Protoboard | 400 ou 830 pontos | 1 |
| Jumpers | Macho-macho e macho-fêmea | ~20 |

### Pinagem

```
GPIO 8  (Pin 11)  → LED 0  (LSB)
GPIO 9  (Pin 12)  → LED 1
GPIO 10 (Pin 14)  → LED 2
GPIO 11 (Pin 15)  → LED 3
GPIO 12 (Pin 16)  → LED 4
GPIO 13 (Pin 17)  → LED 5
GPIO 14 (Pin 19)  → LED 6
GPIO 15 (Pin 20)  → LED 7  (MSB)
GPIO 16 (Pin 21)  → Botão Count (pull-up, active low)
GPIO 17 (Pin 22)  → Botão Reset (pull-up, active low)
```

Cada LED deve ter o ânodo no GPIO, o cátodo no resistor de 330 Ω e o resistor no GND.

---

## Arquitetura

```
┌──────────────────────┐       USB CDC (115200)       ┌─────────────────────┐
│  Raspberry Pi Pico   │ ◄══════════════════════╤══► │   PC (Python 3)     │
│  ┌───────────────┐   │  serial / print (stdin) │   │  ┌──────────────┐   │
│  │   main.py     │   │                         │   │  │ server.py    │   │
│  │  (MicroPython)│   │                         │   │  │ (pyserial)   │   │
│  └───────────────┘   │                         │   │  └──────┬───────┘   │
│         │            │                         │   │         │ HTTP      │
│         ▼            │                         │   │         ▼           │
│   ┌──── 8 LEDs ──┐   │                         │   │  ┌──────────────┐   │
│   │ Botão Count  │   │                         │   │  │ index.html   │   │
│   │ Botão Reset  │   │                         │   │  │ (GUI web)    │   │
│   └──────────────┘   │                         │   │  └──────────────┘   │
└──────────────────────┘                         │   └─────────────────────┘
```

- **Pico (main.py)**: polling não-bloqueante dos botões com debounce de 50ms, comandos via serial, atualização dos LEDs.
- **PC (server.py)**: detecta o Pico automaticamente via `PING`/`PONG`, faz ponte entre serial e HTTP. Servidor local em `127.0.0.1:8000`.
- **Browser (index.html)**: GUI com LEDs clicáveis, entrada de valor, auto-incremento, e painel educativo sobre binário.

---

## Instalação e uso

### 1. Gravar o firmware no Pico

Certifique-se de que o Pico está com o firmware **MicroPython** (não CircuitPython). Baixe em [micropython.org](https://micropython.org/download/rp2-pico/) e siga as instruções oficiais.

### 2. Deploy do código

```bash
# Com o Pico conectado via USB
mpremote cp main.py :
mpremote reset
```

### 3. Montar o circuito

Conecte LEDs, resistores e botões conforme a pinagem acima.

### 4. Iniciar o servidor no PC

```bash
pip install pyserial
python host/server.py           # auto-detect da porta serial
python host/server.py COM5      # ou especifique a porta manualmente
```

O navegador abrirá automaticamente em `http://127.0.0.1:8000`.

---

## Como usar

### Com os botões físicos

- **Botão Count (GPIO 16)**: incrementa o contador em 1 (mod 256).
- **Botão Reset (GPIO 17)**: zera o contador.

### Pela interface web

- **LEDs**: clique em um LED para ligar/desligar individualmente.
- **Input + Ir**: digite um valor de 0 a 255 e clique em "Ir".
- **+1 / −1 / +10 / −10**: incremento/decremento rápido.
- **Resetar**: volta para 0.
- **Auto**: incrementa automaticamente a cada 500ms.
- **Painel educativo**: explica potências de 2 e conversão binário-decimal.

### Pela serial (via script)

```
SET:42    → define contador para 42
INC       → incrementa em 1
RESET     → zera
TOGGLE:3  → alterna LED 3
GET       → requisita estado atual
PING      → health check (responde PONG)
```

---

## Protocolo serial

**Baud rate**: 115200 · **USB CDC** · **Polling não-bloqueante**

### Pico → PC

```
STATE:<counter>:<8-led-bits>
```

Enviado a cada mudança de estado (botão físico ou comando serial).

### PC → Pico

Comandos via `sys.stdin` com `select.poll(0)` (lê apenas quando há dado disponível).

---

## Estrutura do projeto

```
bitcounter-pico/
├── main.py           # Firmware do Pico (MicroPython)
├── host/
│   ├── server.py     # Servidor HTTP/serial bridge (Python)
│   └── index.html    # Interface web (HTML/CSS/JS)
├── README.md
└── AGENTS.md         # Notas para agentes de IA (opencode)
```

---

## Personalização

- **Trocar pinos dos LEDs**: edite `LED_PINS` em `main.py` (linha 6).
- **Velocidade de debounce**: altere `DEBOUNCE_MS` em `main.py` (linha 9).
- **Porta do servidor HTTP**: defina a variável de ambiente `PORT` (ex.: `set PORT=3000` no Windows).
- **Intervalo de polling da GUI**: altere o `setInterval(fetchState, 60)` em `index.html` (linha 439).

---

## Desenvolvimento

Projeto sem dependências de build, sem testes automatizados, sem linter. A única dependência PC-side é `pyserial`.

### Dicas conhecidas

- **Edge detection**: o `DebouncedButton` detecta borda de descida (`s != prev and s == 0`). Siga esse padrão ao adicionar botões.
- **Contador**: usa `(counter + 1) % 256` (mod 256, não clamping). `send_state()` lê os pinos dos LEDs, não a variável `counter` — ambos são mantidos em sincronia.
- **Serial quirk**: `SER.setDTR(False)` é chamado após abrir a porta serial para evitar reset automático em algumas placas RP2040.

---

## Licença

MIT
