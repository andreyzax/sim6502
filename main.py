#!/usr/bin/env python3
"""
Default driver code and entry point for the emulator.

This assembles a simple apple 1 like system with wozmon, apple basic and a demo program.
"""

from argparse import ArgumentParser

import config
from apple_one import Keyboard, Video
from cpu import CPU, CPUTrap
from memory import MemoryMap, RamSegment, RomSegment


def process_arguments() -> None:
    parser = ArgumentParser()
    parser.add_argument("--metrics", "-m", action="store_true", help="Enable runtime metrics collection")
    parser.add_argument(
        "--trap-on-brk", "-tb", action="store_true", help="Raise (emulator) exception and break out of run loop on BRK instructions"
    )
    parser.add_argument("--backend", "-b", action="store", default="terminal", help="UI backend")
    parser.add_argument("--tty", "-t", action="store", default=None, help="tty device for the terminal backend")

    args = parser.parse_args()
    config.enable_runtime_perf_metrics = args.metrics
    config.trap_brk = args.trap_on_brk
    config.backend = args.backend
    if config.backend == "terminal":  # We only support alternative tty devices with the "terminal" backend
        config.terminal_device = args.tty


def trap_handler(cpu: CPU):
    flags = (
        "#" if flag else " "
        for flag in (cpu.p.negative, cpu.p.overflow, True, True, cpu.p.decimal, cpu.p.interrupt_disable, cpu.p.zero, cpu.p.carry)
    )
    flags_str = "".join(flags)
    print(f"""\nExecution stopped:
        pc=0x{cpu.pc:X}
        ins={cpu._decode()}
        s=0x{cpu.s:X}
        a=0x{cpu.a:X},x=0x{cpu.x:X},y=0x{cpu.y:X}
        flags:   NV-BDIZC
                 {flags_str}
        """)


def main():
    """Emulate apple 1 system."""
    process_arguments()

    monitor_rom = RomSegment.from_binary_file(0xFF00, "bin/wozmon.bin")
    basic_rom = RomSegment.from_binary_file(0xE000, "bin/basic.bin")
    mm = MemoryMap(RamSegment(0, 0x7FFF), Video(), Keyboard(), monitor_rom, basic_rom)
    reset_addr = mm[0xFFFD] << 8 | mm[0xFFFC]
    cpu = CPU(memory=mm, pc=reset_addr)
    if isinstance(mm.hardware_map[0], Keyboard):
        mm.hardware_map[0].on_reset = cpu.reset

    with open("bin/mandelbrot-65.bin", "rb") as f:
        cpu.load(0x280, f)

    try:
        cpu.run()
    except CPUTrap as trap:
        trap_handler(trap.cpu)


if __name__ == "__main__":
    main()
