"""
Micropython (Raspberry Pi Pico)
2022/1/12     DENGFEI
lcd.Display() Only 94 limited characters in fonts can be displayed
"""

import machine
import time
import lcd128_32_fonts
cursor = [0, 0]


class lcd128_32:

    def __init__(self, dt, clk, bus, addr):
        self.addr = addr
        self.i2c = machine.I2C(bus, sda=machine.Pin(dt), scl=machine.Pin(clk))
        self.Init()

    def WriteByte_command(self, cmd):
        self.reg_write(0x00, cmd)

    def WriteByte_dat(self, dat):
        self.reg_write(0x40, dat)

    def reg_write(self, reg, data):
        msg = bytearray()
        msg.append(data)
        self.i2c.writeto_mem(self.addr, reg, msg)

    def Init(self):
        time.sleep(0.01)
        self.WriteByte_command(0xe2)
        time.sleep(0.01)
        self.WriteByte_command(0xa3)
        self.WriteByte_command(0xa0)
        self.WriteByte_command(0xc8)
        self.WriteByte_command(0x22)
        self.WriteByte_command(0x81)
        self.WriteByte_command(0x35)
        self.WriteByte_command(0x2c)
        self.WriteByte_command(0x2e)
        self.WriteByte_command(0x2f)
        self.Clear()
        self.WriteByte_command(0xff)
        self.WriteByte_command(0x72)
        self.WriteByte_command(0xfe)
        self.WriteByte_command(0xd6)
        self.WriteByte_command(0x90)
        self.WriteByte_command(0x9d)
        self.WriteByte_command(0xaf)
        self.WriteByte_command(0x40)

    def Clear(self):
        for i in range(4):
            self.WriteByte_command(0xb0 + i)
            self.WriteByte_command(0x10)
            self.WriteByte_command(0x00)
            for j in range(128):
                self.WriteByte_dat(0x00)

    def Cursor(self, y, x):
        if x > 17:
            x = 17
        if y > 3:
            y = 3
        cursor[0] = y
        cursor[1] = x

    def WriteFont(self, num):
        for item in lcd128_32_fonts.textFont[num]:
            self.WriteByte_dat(item)

    def Display(self, s):
        self.WriteByte_command(0xb0 + cursor[0])
        self.WriteByte_command(0x10 + cursor[1] * 7 // 16)
        self.WriteByte_command(0x00 + cursor[1] * 7 % 16)
        for num in range(len(s)):
            c = s[num]
            if '0' <= c <= '9': self.WriteFont(ord(c) - 48)
            elif 'a' <= c <= 'z': self.WriteFont(ord(c) - 87)
            elif 'A' <= c <= 'Z': self.WriteFont(ord(c) - 29)
            else:
                m = {'!': 62, '"': 63, '#': 64, '$': 65, '%': 66, '&': 67,
                     "'": 68, '(': 69, ')': 70, '*': 71, '+': 72, ',': 73,
                     '-': 74, '/': 75, ':': 76, ';': 77, '<': 78, '=': 79,
                     '>': 80, '?': 81, '@': 82, '{': 83, '|': 84, '}': 85,
                     '~': 86, ' ': 87, '.': 88, '^': 89, '_': 90, '`': 91,
                     '[': 92, '\\': 93, ']': 94}
                if c in m:
                    self.WriteFont(m[c])
