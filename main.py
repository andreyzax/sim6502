#!/usr/bin/env python3
"""
Default driver code and entry point for the emulator.

This assembles a simple apple 1 like system with wozmon, apple basic and a demo program.
"""

from argparse import ArgumentParser

import apple_one
import headless
from config import settings


def process_arguments() -> None:
    """Process command line arguments and set parameter values in settings object."""
    parser = ArgumentParser()
    parser.add_argument("--profile", "-p", action="store", help="Select a settings profile from the settings file.")
    parser.add_argument("--metrics", "-m", action="store_true", help="Enable runtime metrics collection")
    parser.add_argument("--trap-brk", "-tb", action="store_true", help="Raise (emulator) exception and break out of run loop on BRK instructions")
    parser.add_argument("--backend", "-b", action="store", default=None, help="UI backend")
    parser.add_argument("--system", "-s", action="store", default=None, help="Emulation target")
    parser.add_argument("--tty", "-t", action="store", default=None, help="tty device for the terminal backend")

    args = parser.parse_args()
    args_dict = vars(args)

    if args.profile:
        settings.setenv(args.profile)

    for arg in ("metrics", "trap_brk", "system", "backend", "tty"):
        if args_dict[arg]:
            settings[arg] = args_dict[arg]


def main() -> None:
    """
    Entry point for the emulator.

    Generic configuration processing, runtime selection and start up.
    """
    process_arguments()

    if settings.system == "apple1":
        if settings.backend == "terminal":
            runtime = apple_one.TerminalRuntime(settings)
        elif settings.backend == "tui":
            runtime = apple_one.TuiRuntime(settings)
        else:
            raise RuntimeError(f"Backend ({settings.backend}) is not supported.")
    elif settings.system == "headless":
        if settings.backend == "tui":
            runtime = headless.TuiRuntime(settings.start_address)
        else:
            raise RuntimeError(f"Backend ({settings.backend}) is not supported.")
    else:
        raise RuntimeError(f"System ({settings.system}) is not supported.")

    runtime.run()


if __name__ == "__main__":
    main()
