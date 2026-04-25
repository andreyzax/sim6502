#!/usr/bin/env python

from cpu import CPU
from memory import MemoryMap, RomSegment


def main():
    rom = RomSegment.from_bytes(4, bytes_source=(b"\xa9\x01\x8d\x00\x02\xa9\x05\x8d\x01\x02\xa9\x08\x8d\x02\x02\x00"))
    mm = MemoryMap(allocation_list=((0, 4),), additional_memory_segments=(rom,))
    cpu = CPU(memory=mm, pc=0x400)

    cpu.run()


if __name__ == "__main__":
    main()
