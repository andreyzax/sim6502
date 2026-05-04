#!/usr/bin/env python3
"""
Default driver code and entry point for the emulator.

This assembles a simple apple 1 like system with wozmon, apple basic and a demo program.
"""

from argparse import ArgumentParser

from textual.app import App, ComposeResult
from textual.widgets import Footer

import config
from apple_one.system import TerminalRuntime, TuiRuntime


def process_arguments() -> None:
    """Process command line arguments and set parameter values in config module."""
    parser = ArgumentParser()
    parser.add_argument("--metrics", "-m", action="store_true", help="Enable runtime metrics collection")
    parser.add_argument("--trap-on-brk", "-tb", action="store_true", help="Raise (emulator) exception and break out of run loop on BRK instructions")
    parser.add_argument("--backend", "-b", action="store", default="terminal", help="UI backend")
    parser.add_argument("--tty", "-t", action="store", default=None, help="tty device for the terminal backend")

    args = parser.parse_args()
    config.enable_runtime_perf_metrics = args.metrics
    config.trap_brk = args.trap_on_brk
    config.backend = args.backend
    if config.backend == "terminal":  # We only support alternative tty devices with the "terminal" backend
        config.terminal_device = args.tty


class UI(App):
    CSS_PATH = "style.tcss"

    BINDINGS = [("ctrl+c", "quit", "Quit immediately")]

    def __init__(self, runtime: TuiRuntime) -> None:
        super().__init__()

        self.runtime = runtime

    def compose(self) -> ComposeResult:
        yield self.runtime.console
        yield Footer()

    def _tick(self):
        self.runtime.run_for(5000)
        self.runtime.console.flush()

    def on_mount(self) -> None:
        self.set_interval(1 / 60, self._tick, pause=False)


if __name__ == "__main__":
    process_arguments()

    if config.backend == "terminal":
        runtime = TerminalRuntime()
        runtime.run()
    elif config.backend == "tui":
        ui = UI(TuiRuntime())
        ui.run()
    else:
        raise RuntimeError(f"Backend ({config.backend}) is not supported.")
