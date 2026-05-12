"""
This module implements the TUI ui shell for the headless backend.

It implements the TUI interface with the textual package.
Classes:
    UI - tui emulator shell.

"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Log, Static

import headless.system as system
from tui import HelpBar


class UI(App):
    """The Headless tui interface shell."""

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

        if runtime.system.collect_metrics:
            self._metrics_widget = Static(id="metrics")
        self._registers_widget = Static(id="registers")
        self._flags_widget = Static(id="flags")
        if runtime.system.collect_metrics:
            self._status_bar_widget = Horizontal(self._metrics_widget, self._registers_widget, self._flags_widget, id="status_bar")
        else:
            self._status_bar_widget = Horizontal(self._registers_widget, self._flags_widget, id="status_bar")

    def compose(self) -> ComposeResult:
        """Assemble the shell."""
        yield HelpBar()
        yield Log(id="error-log")
        yield self._status_bar_widget

    def _short_tick(self) -> None:
        """Timer "tick", execute the runtime for a bounded limit of instructions and flush the console."""
        self._runtime.run_for(1000)

    def _tick(self) -> None:
        self._registers_widget.update(
            f"a={self._runtime.cpu.a:02X}, x={self._runtime.cpu.x:02X}, y={self._runtime.cpu.y:02X}\nsp={self._runtime.cpu.s:02X}, pc={self._runtime.cpu.pc:04X}"
        )
        self._flags_widget.update(f"flags:   NV-BDIZC\n         {str(self._runtime.cpu.p)}")

    def _long_tick(self) -> None:
        if self._runtime.system.collect_metrics:
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
        if self._runtime.system.collect_metrics:
            self._metrics_widget.display = not self._metrics_widget.display

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Disable the metrics toggle command if metrics are disabled."""
        return not (action == "metrics_toggle" and not self._runtime.system.collect_metrics)

    def action_resume(self) -> None:
        """Resume the emulator."""
        self._runtime.resume()
