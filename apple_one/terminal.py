"""
This module is the tty backend for the apple 1 console.

It implements the console using a tty interface, very little demands are placed on
the underlying tty device. It only needs to display ascii characters and process new line
characters correctly. There must also be a way to do non blocking polling for key presses.
Specifically, this backend doesn't use any cursor navigation, text formatting, color or any other escape sequences.
"""

import atexit
import select
import sys
import termios
import tty
from io import FileIO, TextIOWrapper

import config

from .api import DisplayBackend, KeyboardBackend

_original_tty_settings = None
_input = sys.stdin
_output = sys.stdout


def restore_terminal(terminal: TextIOWrapper) -> None:
    """Restore tty to original settings."""
    global _original_tty_settings
    if _original_tty_settings:
        termios.tcsetattr(terminal.fileno(), termios.TCSADRAIN, _original_tty_settings)
        _original_tty_settings = None


def init_backend(terminal: FileIO | TextIOWrapper | None = None):
    """
    Setup the tty to the correct state for apple 1 emulation.

    Also register an atexit cleanup handler to restore the terminal to it's old state
    """
    global _original_tty_settings, _output, _input

    if terminal is None:
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            raise RuntimeError("Console backend is not supported without a tty attached")

        assert isinstance(_output, TextIOWrapper)
        _output.reconfigure(write_through=True)
    else:
        if not (isinstance(terminal, FileIO) and terminal.isatty()):
            raise RuntimeError("Console backend is not supported without a tty attached")

        _input = TextIOWrapper(terminal)
        _output = TextIOWrapper(terminal)

    assert isinstance(_input, TextIOWrapper)
    atexit.register(restore_terminal, _input)

    _original_tty_settings = termios.tcgetattr(_input.fileno())
    tty.setcbreak(_input.fileno())


class TerminalKeyboardBackend(KeyboardBackend):
    def kb_input_ready(self) -> bool:
        return select.select([_input.fileno()], [], [], 0) == ([_input.fileno()], [], [])

    def get_char(self) -> str:
        global _input

        return _input.read(1)


class TerminalDisplayBackend(DisplayBackend):
    def put_char(self, char: int) -> None:
        global _output

        _output.write(chr(char))
        _output.flush()


if __name__ != "__main__":  # only run on *import* not as a stand alone script!
    if config.terminal_device:
        terminal = open(config.terminal_device, "r+b", buffering=0)
        init_backend(terminal)
    else:
        init_backend()
