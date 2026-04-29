# **sim6502**

A simple MOS 6502 CPU emulator written in Python.

# **Overview**

## This project aims to implement a functional emulator for the classic **6502 microprocessor**, focusing on correctness and clarity over performance.

## **Status:**

- Emulator core, complete
- Apple 1 base hardware, functional
- Wozmon, Apple BASIC & several third party applications confirmed as working

## **Goals:**

- [x] Implement core CPU registers and flags
- [x] Implement emulated ram and system memory map
- [x] Add instruction decoding
- [x] Implement addressing modes
- [x] Support full instruction set - (Documented opcodes only for now)
- [ ] Decimal mode (BCD arithmetic)
- [x] Add test suite
- [x] Basic CLI or debugging interface
- [ ] Interactive TUI

## **Long-term goals:**

- Multiple interfaces, TUI & GUI.
- Multiple emulation targets (Apple ||, Commodore 64, NES,...).

## **Usage:**

run `python main.py`

## **Development:**

Requirements:

- Python 3.11 and above
- [poe the poet](https://poethepoet.natn.io/) - to run the automation tasks

### **Clone the repository:**

```bash
git clone <repo-url>
cd <repo-name>
```

### **Run the test suite:**

```bash
poe test # Test on system python

poe test-py311 # Test specific python versions
poe test-py312
poe test-py3**

poe test-all # Test all defined versioned tests
```

### **Run the profiler:**

```bash
poe profile # Profile run statistics are kept in .prof directory
```
