"""
This module implements the apple 1 console.

Classes:
    Keyboard - Implements the apple 1 keyboard interface.
    Video - Implements the apple 1 video interface.
"""

from collections import deque
from contextlib import suppress
from typing import Callable

from apple_one.api import DisplayBackend, KeyboardBackend
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
    """The keyboard interface."""

    class KBD(Register):
        """KBD register, keyboard input characters."""

        def __init__(self, device: "Keyboard") -> None:
            """Initialize register state."""
            self.device = device
            self.last_char = 0

        def read(self) -> int:
            """Read characters from the register."""
            with suppress(IndexError):
                self.last_char = self.device.input_queue.popleft() | 0x80
                if not self.device.input_queue:
                    self.device.input_ready = False

            return self.last_char

        def write(self, value: int) -> None:
            """Write to the register, a no op stub method."""
            pass

    class KBDCR(Register):
        """KBDCR register, keyboard input availability."""

        def __init__(self, device: "Keyboard") -> None:
            """Initialize register state."""
            self.device = device

        def read(self) -> int:
            """Read from the register, high bit is set when input is available."""
            return 0x80 if self.device.input_ready else 0x0

        def write(self, value: int) -> None:
            """Write to the register, a no op stub method."""
            pass

    def __init__(self, backend: KeyboardBackend, on_reset: Callable[[], None] | None = None):
        """Consume implementation backend and initialize keyboard state."""
        super().__init__(0xD010, 2)

        self.registers = {KBD: self.KBD(self), KBDCR: self.KBDCR(self)}
        self.input_ready = False
        self.input_queue: deque[int] = deque()
        self.on_reset = on_reset
        self.backend = backend

    def poll_host(self) -> None:
        """Poll for input from the implementation backend."""
        if self.backend.kb_input_ready():
            ch = ord(self.backend.get_char().upper())
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
        """Memory mapped io interface, route reads to the correct registers."""
        self._validate_address(address)

        for reg_address, register in self.registers.items():
            if reg_address == address:
                return register.read()

        raise IndexError

    def __setitem__(self, address: int, value: int) -> None:
        """Memory mapped io interface, route writes to the correct registers."""
        self._validate_address(address)

        if address in self.registers:
            return
        else:
            raise IndexError


class Video(Device):
    """The video interface."""

    class DSP(Register):
        """DSP register, output characters to the screen."""

        def __init__(self, put_char: Callable[[int], None]) -> None:
            """
            Initialize register state.

            Attach the backend implementation put_char() function.
            """
            self.cursor = 0
            self.put_char = put_char

        def read(self) -> int:
            """Read data from register, dummy stub function."""
            return 0x0

        def write(self, value: int) -> None:
            """Output characters to the screen."""
            ch = value & 0x7F
            if ch == KEY_CR:
                self.put_char(ord("\n"))
                self.cursor = 0
                return

            if self.cursor > LAST_COLUMN:
                self.put_char(ord("\n"))
                self.cursor = 0

            self.put_char(ch)
            self.cursor += 1

    class DSPCR(Register):
        """
        DSPCR register, get video device status.

        We don't fully emulate the apple 1 hardware state,
        so this register is a stub dummy register which always returns
        a ready for output status.
        """

        def __init__(self) -> None:
            """Initialize register state."""
            self.value = 0x0

        def read(self) -> int:
            """Read data from register, dummy stub function."""
            return self.value

        def write(self, value: int) -> None:
            """Write data from register, dummy stub function."""
            self.value = value

    def __init__(self, backend: DisplayBackend) -> None:
        """Consume implementation backend and initialize video state."""
        super().__init__(0xD012, 2)

        self.backend = backend
        self.registers = {DSP: self.DSP(self.backend.put_char), DSPCR: self.DSPCR()}

    def poll_host(self) -> None:
        """Dummy stub for output only device."""
        pass

    def __getitem__(self, address: int) -> int:
        """Memory mapped io interface, route reads to the correct registers."""
        self._validate_address(address)

        for reg_address, register in self.registers.items():
            if reg_address == address:
                return register.read()

        raise IndexError

    def __setitem__(self, address: int, value: int) -> None:
        """Memory mapped io interface, route writes to the correct registers."""
        self._validate_address(address)

        for reg_address, register in self.registers.items():
            if reg_address == address:
                return register.write(value)

        raise IndexError
