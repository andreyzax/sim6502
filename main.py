#!/usr/bin/env python3
"""
Default driver code and entry point for the emulator.

This assembles a simple apple 1 like system with wozmon, apple basic and a demo program.
"""

from argparse import ArgumentParser

# from textual import events
# from textual.app import ComposeResult
import config
from apple_one.system import AppleOne

# from apple_one.tui import TTY
from cpu import CPU, CPUTrap


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


def trap_handler(cpu: CPU):
    """Handle cpu traps, currently only gets triggered if `config.trap_brk` is true."""
    flags = ("#" if flag else " " for flag in (cpu.p.negative, cpu.p.overflow, True, True, cpu.p.decimal, cpu.p.interrupt_disable, cpu.p.zero, cpu.p.carry))
    flags_str = "".join(flags)
    print(f"""\nExecution stopped:
        pc=0x{cpu.pc:X}
        ins={cpu._decode()}
        s=0x{cpu.s:X}
        a=0x{cpu.a:X},x=0x{cpu.x:X},y=0x{cpu.y:X}
        flags:   NV-BDIZC
                 {flags_str}
        """)


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


def terminal_main():
    """Emulate apple 1 system with a terminal backend."""
    from apple_one import terminal

    if config.terminal_device:
        device = open(config.terminal_device, "r+b", buffering=0)
        terminal.init_backend(device)
    else:
        terminal.init_backend()

    system = AppleOne(display_backend=terminal.TerminalDisplayBackend(), keyboard_backend=terminal.TerminalKeyboardBackend())

    try:
        res = system.run()
        if res:
            print("\nExecution stopped.")
            print(f"Instructions: {res.instructions}, ips: {res.ips:,}, average instruction time: {res.avg_ins_time:.3f}us")
    except CPUTrap as trap:
        trap_handler(trap.cpu)


if __name__ == "__main__":
    process_arguments()
    if config.backend == "terminal":
        terminal_main()
    # elif config.backend == "tui":
    #    tui_main()
    else:
        raise RuntimeError(f"Backend ({config.backend}) is not supported")
