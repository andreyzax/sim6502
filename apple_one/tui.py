"""Implement the TUI hardware backend and TUI runtime."""

from collections import deque
from typing import Callable

from rich.text import Text
from textual.app import RenderResult
from textual.events import Key
from textual.widget import Widget

from apple_one.api import DisplayBackend, KeyboardBackend


class ConsoleWidget(Widget):
    can_focus = True

    def __init__(self, max_lines=500, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._lines: deque[str] = deque(maxlen=max_lines)
        self._inject_char: Callable[[str], None] | None = None
        self._dirty = False

        self.border_title = "Console"

    def flush(self) -> None:
        if self._dirty:
            self.refresh()
            self._dirty = False

    @property
    def inject_char(self) -> Callable[[str], None] | None:
        return self._inject_char

    @inject_char.setter
    def inject_char(self, value: Callable[[str], None]) -> None:
        self._inject_char = value

    def display_char(self, char: str) -> None:
        if char == "\n":
            self._lines.append("")
        else:
            self._lines[-1] += char

        self._dirty = True

    def on_key(self, event: Key) -> None:
        if self.inject_char:  # we could be called without a set self.inject_char, need to guard against that.
            if event.is_printable:
                assert event.character is not None
                self.inject_char(event.character)
            if event.name == "enter":
                self.inject_char("\n")
            if event.name in ("ctrl_r", "ctrl_d", "escape"):
                assert event.character is not None
                self.inject_char(event.character)
        else:
            pass  # Since we don't have a way to pass input to the emulator, we just do nothing

    def render(self) -> RenderResult:
        height = max(1, self.content_size.height)
        nlines = len(self._lines)
        visible = nlines - height
        if height == 0:
            return ""

        return Text("\n".join([line for line_number, line in enumerate(self._lines) if line_number >= visible]))


class TuiKeyboardBackend(KeyboardBackend):
    """Apple 1 keyboard implementation using a textual tui widget."""

    def __init__(self, console: ConsoleWidget) -> None:
        """Consume a ConsoleWidget and init internal state."""
        self.console = console
        self.console.inject_char = self.inject_char
        self._input_queue = deque()
        self.last_char = "\x00"

    def kb_input_ready(self) -> bool:
        """Poll for input from the widget."""
        return bool(self._input_queue)

    def get_char(self) -> str:
        """Read a character from the widget."""
        if self._input_queue:
            self.last_char = self._input_queue.popleft()

        return self.last_char

    def inject_char(self, char: str) -> None:
        """Inject an input character into the backend."""
        self._input_queue.append(char)


class TuiDisplayBackend(DisplayBackend):
    """Apple 1 display implementation using a textual tui widget."""

    def __init__(self, console: ConsoleWidget) -> None:
        """Consume a ConsoleWidget and init internal state."""
        self.console = console

    def put_char(self, char: int) -> None:
        """Write a character to the console widget."""
        self.console.display_char(chr(char))
