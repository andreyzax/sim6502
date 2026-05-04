#!/usr/bin/env python3
"""
Default driver code and entry point for the emulator.

This assembles a simple apple 1 like system with wozmon, apple basic and a demo program.
"""

from argparse import ArgumentParser

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


def main() -> None:
    """
    Entry point for the emulator.

    Generic configuration processing, runtime selection and start up.
    """
    process_arguments()

    if config.backend == "terminal":
        runtime = TerminalRuntime()
    elif config.backend == "tui":
        runtime = TuiRuntime()
    else:
        raise RuntimeError(f"Backend ({config.backend}) is not supported.")
    runtime.run()


if __name__ == "__main__":
    main()
