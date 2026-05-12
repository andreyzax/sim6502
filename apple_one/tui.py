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

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

import apple_one.system as system
from apple_one.api import DisplayBackend, KeyboardBackend
from tui import ConsoleWidget, HelpBar, MemoryViewer


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

        if self._runtime.system.collect_metrics:
            self._metrics_widget = Static(id="metrics")
        self._registers_widget = Static(id="registers")
        self._flags_widget = Static(id="flags")
        self._mempry_viewer = MemoryViewer(self._runtime.memory)
        if self._runtime.system.collect_metrics:
            self._status_bar_widget = Horizontal(self._metrics_widget, self._registers_widget, self._flags_widget, id="status_bar")
        else:
            self._status_bar_widget = Horizontal(self._registers_widget, self._flags_widget, id="status_bar")

    def compose(self) -> ComposeResult:
        """Assemble the shell."""
        yield HelpBar()
        yield Horizontal(self._runtime.console, self._mempry_viewer)
        yield self._status_bar_widget

    def _tick(self) -> None:
        self._runtime.run_for(16700)
        self._runtime.console.flush()
        self._registers_widget.update(
            f"a={self._runtime.cpu.a:02X}, x={self._runtime.cpu.x:02X}, y={self._runtime.cpu.y:02X}\nsp={self._runtime.cpu.s:02X}, pc={self._runtime.cpu.pc:04X}"
        )
        self._flags_widget.update(f"flags:   NV-BDIZC\n         {str(self._runtime.cpu.p)}")

    def _long_tick(self) -> None:
        self._mempry_viewer.refresh()
        if self._runtime.system.collect_metrics:
            self._metrics_widget.update(str(self._runtime.metrics))

    def on_mount(self) -> None:
        """Standard textual call back, start the runtime timer here."""
        self.set_interval(0.0167, self._tick, name="tick", pause=False)
        self.set_interval(1, self._long_tick, name="long_tick", pause=False)

        self._tick()
        self._long_tick()

    def action_stop(self) -> None:
        """Pause the emulator."""
        self._runtime.stop()

    def action_metrics_toggle(self) -> None:
        """Toggle metrics widget display."""
        if self._runtime.system.collect_metrics:
            self._metrics_widget.display = not self._metrics_widget.display

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Disable the metrics toggle command if metrics are disabled."""
        return not (action == "metrics_toggle" and not self._runtime.system.collect_metrics)

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
