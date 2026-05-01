#!/usr/bin/env python3

from argparse import ArgumentParser

import config
from apple_one import Keyboard, Video
from cpu import CPU, CPUTrap
from memory import MemoryMap, RamSegment, RomSegment


def process_arguments() -> None:
    parser = ArgumentParser()
    parser.add_argument("--metrics", "-m", action="store_true", help="Enable runtime metrics collection")
    parser.add_argument(
        "--trap-on-brk", "-b", action="store_true", help="Raise (emulator) exception and break out of run loop on BRK instructions"
    )

    args = parser.parse_args()
    config.enable_runtime_perf_metrics = args.metrics
    config.trap_brk = args.trap_on_brk


def trap_handler(cpu: CPU):
    print(f"""\nExecution stopped:
        pc=0x{cpu.pc:X}
        ins={cpu._decode()}
        s=0x{cpu.s:X}
        a=0x{cpu.a:X},x=0x{cpu.x:X},y=0x{cpu.y:X}
        flags:   NV-BDIZC
                 {"#" if cpu.p.negative else " "}{"#" if cpu.p.overflow else " "}##{"#" if cpu.p.decimal else " "}{"#" if cpu.p.interrupt_disable else " "}{"#" if cpu.p.zero else " "}{"#" if cpu.p.carry else " "}
        """)

    # print("Memory Dump:\n--------------------------------------")
    # print(ctx.cpu.memory.dump())


def main():
    """Emulate apple 1 system."""
    process_arguments()

    monitor_rom = RomSegment.from_binary_file(0xFF00, "bin/wozmon.bin")
    basic_rom = RomSegment.from_binary_file(0xE000, "bin/basic.bin")
    mm = MemoryMap(RamSegment(0, 0x7FFF), Video(), Keyboard(), monitor_rom, basic_rom)
    reset_addr = mm[0xFFFD] << 8 | mm[0xFFFC]
    cpu = CPU(memory=mm, pc=reset_addr)
    with open("bin/mandelbrot-65.bin", "rb") as f:
        cpu.load(0x280, f)

    try:
        cpu.run()
    except CPUTrap as trap:
        trap_handler(trap.cpu)


if __name__ == "__main__":
    main()
