"""
This module implements the TUI hardware backends and ui shell for the apple 1.

It implements the TUI interface with the textual package.
Classes:
    TuiKeyboardBackend - tui Keyboard backend.
    TuiDisplayBackend - tui Display backend.
    ConsoleWidget - Apple 1 console tui implementation.
    UI - tui emulator shell.

"""

from collections import deque
from typing import Callable

from rich.text import Text
from textual.app import App, ComposeResult, RenderResult
from textual.containers import Horizontal
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Static

import apple_one.system as system
import config
from apple_one.api import DisplayBackend, KeyboardBackend


class ConsoleWidget(Widget):
    """
    A textual tui widget that models an Apple 1 console.

    Used by the tui hardware backends and embedded inside the tui runtime shell.
    """

    can_focus = True

    def __init__(self, max_lines=500, *args, **kwargs):
        """
        Initialize the console.

        Accepts max_lines to set scrollback buffer size. Also accepts any generic
        textual Widget arguments (id, class,...)
        """
        super().__init__(*args, **kwargs)

        self._lines: deque[str] = deque(maxlen=max_lines)
        self._inject_char: Callable[[str], None] | None = None
        self._dirty = False

        self.border_title = "Console"

    def flush(self) -> None:
        """
        Sync visible console content with internal buffer.

        Writes to the console won't be shown on screen without calling this.
        """
        if self._dirty:
            self.refresh()
            self._dirty = False

    @property
    def inject_char(self) -> Callable[[str], None] | None:
        """inject_char property."""
        return self._inject_char

    @inject_char.setter
    def inject_char(self, value: Callable[[str], None]) -> None:
        """
        inject_char setter.

        This property is a callable which accepts a one char string and is responsible
        to pass console input to the emulated keyboard interface.
        """
        self._inject_char = value

    def display_char(self, char: str) -> None:
        """
        Add a character to the console buffer, handles new line processing.

        This method will not display the new output immediately, flush() must be called
        to sync the internal buffer with the rendered text.
        """
        if char == "\n":
            self._lines.append("")
        else:
            self._lines[-1] += char

        self._dirty = True

    def on_key(self, event: Key) -> None:
        """
        Respond to textual keyboard input events and inject them to the emulated keyboard interface.

        Handles carriage return (enter key) and control character processing.
        """
        if self.inject_char:  # we could be called without a set self.inject_char, need to guard against that.
            if event.is_printable:
                assert event.character is not None
                self.inject_char(event.character)
            if event.name == "enter":
                self.inject_char("\n")
            if event.name in ("ctrl_r", "ctrl_d"):
                assert event.character is not None
                self.inject_char(event.character)
        else:
            pass  # Since we don't have a way to pass input to the emulator, we just do nothing

    def render(self) -> RenderResult:
        """
        Render the console buffer into the widget content area.

        Only renders the visible part of the buffer.
        """
        height = max(1, self.content_size.height)
        nlines = len(self._lines)
        visible = nlines - height
        if height == 0:
            return ""

        return Text("\n".join([line for line_number, line in enumerate(self._lines) if line_number >= visible]))


class UI(App):
    """The Apple 1 tui interface shell."""

    CSS_PATH = "style.tcss"

    BINDINGS = [
        ("ctrl+c", "quit", "Quit immediately"),
        ("ctrl+s", "stop", "Stop emulator"),
        ("ctrl+g", "resume", "Resume emulator"),
        ("ctrl+a", "metrics_toggle", "Show/Hide metrics"),
    ]

    def __init__(self, runtime: system.TuiRuntime) -> None:
        """Initialize the interface, accepts a reference to the runtime."""
        super().__init__()

        self._runtime = runtime

        if config.enable_runtime_perf_metrics:
            self._metrics_widget = Static(id="metrics")
        self._registers_widget = Static(id="registers")
        self._flags_widget = Static(id="flags")
        if config.enable_runtime_perf_metrics:
            self._status_bar_widget = Horizontal(self._metrics_widget, self._registers_widget, self._flags_widget, id="status_bar")
        else:
            self._status_bar_widget = Horizontal(self._registers_widget, self._flags_widget, id="status_bar")

    def compose(self) -> ComposeResult:
        """Assemble the shell."""
        yield self._runtime.console
        yield self._status_bar_widget

    def _short_tick(self) -> None:
        """Timer "tick", execute the runtime for a bounded limit of instructions and flush the console."""
        self._runtime.run_for(1000)

    def _tick(self) -> None:
        self._runtime.console.flush()
        self._registers_widget.update(
            f"a={self._runtime.cpu.a:02X}, x={self._runtime.cpu.x:02X}, y={self._runtime.cpu.y:02X}\nsp={self._runtime.cpu.s:02X}, pc={self._runtime.cpu.pc:04X}"
        )
        self._flags_widget.update(f"flags:   NV-BDIZC\n         {str(self._runtime.cpu.p)}")

    def _long_tick(self) -> None:
        if config.enable_runtime_perf_metrics:
            self._metrics_widget.update(str(self._runtime.metrics))

    def on_mount(self) -> None:
        """Standard textual call back, start the runtime timer here."""
        self.set_interval(0.001, self._short_tick, name="short_tick", pause=False)
        self.set_interval(0.0167, self._tick, name="tick", pause=False)
        self.set_interval(1, self._long_tick, name="long_tick", pause=False)

        self._short_tick()
        self._tick()
        self._long_tick()

    def action_stop(self) -> None:
        """Pause the emulator."""
        self._runtime.stop()

    def action_metrics_toggle(self) -> None:
        """Toggle metrics widget display."""
        if config.enable_runtime_perf_metrics:
            self._metrics_widget.display = not self._metrics_widget.display

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Disable the metrics toggle command if metrics are disabled."""
        return not (action == "metrics_toggle" and not config.enable_runtime_perf_metrics)

    def action_resume(self) -> None:
        """Resume the emulator."""
        self._runtime.resume()


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
