"""
This module implements the apple 1 console.

The keyboard and video section are both implemented
"""

import atexit
import select
import sys
import termios
import tty
from collections import deque
from contextlib import suppress
from typing import Callable

from mmio import Device, Register

KBD = 0xD010
KBDCR = 0xD011
DSP = 0xD012
DSPCR = 0xD013

LAST_COLUMN = 39

KEY_CR = 0x0D
KEY_LF = 0x0A
KEY_BACKSLASH = 0x5C
KEY_ESC = 0x1B
KEY_CTRL_R = 0x12


class Keyboard(Device):
    _original_tty_settings = None

    class KBD(Register):
        def __init__(self, device: "Keyboard") -> None:
            self.device = device
            self.last_char = 0

        def read(self) -> int:
            with suppress(IndexError):
                self.last_char = self.device.input_queue.popleft() | 0x80
                if not self.device.input_queue:
                    self.device.input_ready = False

            return self.last_char

        def write(self, value: int) -> None:
            pass

    class KBDCR(Register):
        def __init__(self, device: "Keyboard") -> None:
            self.device = device

        def read(self) -> int:
            return 0x80 if self.device.input_ready else 0x0

        def write(self, value: int) -> None:
            pass

    def __init__(self, on_reset: Callable[[], None] | None = None):
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            raise RuntimeError("Console backend is not supported without a tty attached")

        super().__init__(0xD010, 2)

        atexit.register(self._restore_tty)

        type(self)._original_tty_settings = termios.tcgetattr(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())

        self.registers = {KBD: self.KBD(self), KBDCR: self.KBDCR(self)}
        self.input_ready = False
        self.input_queue: deque[int] = deque()
        self.on_reset = on_reset

    @classmethod
    def _restore_tty(cls):
        if cls._original_tty_settings:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, cls._original_tty_settings)
            cls._original_tty_settings = None

    def _tty_input_ready(self) -> bool:
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def poll_host(self) -> None:
        if self._tty_input_ready():
            ch = ord(sys.stdin.read(1).upper())
            if ch == KEY_LF:
                self.input_queue.append(KEY_CR)
            elif ch == KEY_CTRL_R:
                if self.on_reset:
                    self.on_reset()
                return  # Don't set self.input_ready, we remove ctrl-r from the input stream
            else:
                self.input_queue.append(ch)
            self.input_ready = True

    def __getitem__(self, address: int) -> int:
        self._validate_address(address)

        for reg_address, register in self.registers.items():
            if reg_address == address:
                return register.read()

        raise IndexError

    def __setitem__(self, address: int, value: int) -> None:
        self._validate_address(address)

        if address in self.registers:
            return
        else:
            raise IndexError


class Video(Device):
    class DSP(Register):
        def __init__(self) -> None:
            self.cursor = 0

        def read(self) -> int:
            return 0x0

        def write(self, value: int) -> None:
            ch = value & 0x7F
            if ch == KEY_CR:
                print("\n", end="", flush=True)
                self.cursor = 0
                return

            if self.cursor > LAST_COLUMN:
                print("\n", end="", flush=True)
                self.cursor = 0

            print(chr(ch), end="", flush=True)
            self.cursor += 1

    class DSPCR(Register):
        def __init__(self) -> None:
            self.value = 0x0

        def read(self) -> int:
            return self.value

        def write(self, value: int) -> None:
            self.value = value

    def __init__(self) -> None:
        super().__init__(0xD012, 2)
        self.registers = {DSP: self.DSP(), DSPCR: self.DSPCR()}

    def poll_host(self) -> None:
        pass

    def __getitem__(self, address: int) -> int:
        self._validate_address(address)

        for reg_address, register in self.registers.items():
            if reg_address == address:
                return register.read()

        raise IndexError

    def __setitem__(self, address: int, value: int) -> None:
        self._validate_address(address)

        for reg_address, register in self.registers.items():
            if reg_address == address:
                return register.write(value)

        raise IndexError
