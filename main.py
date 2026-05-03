#!/usr/bin/env python3
"""
Default driver code and entry point for the emulator.

This assembles a simple apple 1 like system with wozmon, apple basic and a demo program.
"""

from argparse import ArgumentParser

import config

# from textual import events
# from textual.app import ComposeResult
from apple_one.system import TerminalRuntime

# from apple_one.tui import TTY


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


# def tui_main():
#    from textual.app import App
#    from textual.containers import HorizontalGroup
#    from textual.widgets import Placeholder
#
#    class UI(App):
#        CSS_PATH = "style.tcss"
#
#        def compose(self) -> ComposeResult:
#            yield HorizontalGroup(TTY(columns=40, lines=24, id="console"), Placeholder("Memory", id="memory_view"))
#            yield Placeholder("Statusbar", id="status_bar")
#
#        def on_key(self, event: events.Key) -> None:
#            if event.is_printable:
#                assert event.character is not None
#                self.query_one(TTY).put_char(ord(event.character))
#            if event.name == "enter":
#                self.query_one(TTY).put_char(0xA)
#
#    UI().run()


if __name__ == "__main__":
    process_arguments()

    if config.backend == "terminal":
        runtime = TerminalRuntime()
    else:
        raise RuntimeError(f"Backend ({config.backend}) is not supported.")

    runtime.run()
