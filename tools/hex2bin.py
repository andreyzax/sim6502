#!/usr/bin/env python3

import enum
import sys

if len(sys.argv) != 2:
    raise RuntimeError(f"Usage: {sys.argv[0]} filename")

with open(f"{sys.argv[1]}") as input, open(f"{sys.argv[1]}.bin", "wb") as output:
    for line_number, line in enumerate(input):
        line = line.strip()
        if len(line) != 2:
            raise RuntimeError("corrupt data on line:", line_number)
        byte = int(line, base=16)
        output.write(bytes([byte]))
