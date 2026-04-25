#!/usr/bin/env python

from cpu import CPU
from memory import MemoryMap, RamSegment, RomSegment


def trap_handler(cpu: CPU):
    print(f"""Execution stopped:
        pc=0x{cpu.pc:X}
        s=0x{cpu.s:X}
        a=0x{cpu.a:X},x=0x{cpu.x:X},y=0x{cpu.y:X}
        flags:   NV-BDIZC
                 {"#" if cpu.p.negative else " "}{"#" if cpu.p.overflow else " "}##{"#" if cpu.p.decimal else " "}{"#" if cpu.p.interrupt_disable else " "}{"#" if cpu.p.zero else " "}{"#" if cpu.p.carry else " "}
        """)

    # print("Memory Dump:\n--------------------------------------")
    # print(ctx.cpu.memory.dump())


def main():
    rom = RomSegment.from_bytes(4, bytes_source=(b"\xa9\x01\x8d\x00\x02\xa9\x05\x8d\x01\x02\xa9\x08\x8d\x02\x02\x00"))
    mm = MemoryMap(RamSegment(0, 4), rom)
    cpu = CPU(memory=mm, pc=0x400)

    cpu.run(trap_handler)


if __name__ == "__main__":
    main()
