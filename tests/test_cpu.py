import pytest

from cpu import CPU, CPUTrap
from memory import MemoryMap
from assembly import Instruction, Operation, AddressMode


@pytest.fixture
def system() -> CPU:
    return CPU(MemoryMap(allocation_list=((0, 16),)))  # 4KiB of ram


@pytest.fixture
def full_mem_system() -> CPU:
    return CPU(MemoryMap(allocation_list=((0, 256),)))


def test_nop(system: CPU):
    cpu = system
    ins = Instruction(op=Operation.NOP, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size


def test_register_instructions(system: CPU):
    cpu = system

    ins = Instruction(op=Operation.TAX, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.a = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.a = 42
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 42
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.a = 180  # -76 in 2's complement
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 180
    assert not cpu.p.zero
    assert cpu.p.negative

    initial_pc = cpu.pc
    cpu.a = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.TXA, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.x = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 42
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 42
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 180  # -76 in 2's complement
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 180
    assert not cpu.p.zero
    assert cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.TYA, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.y = 42
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 42
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.y = 180  # -76 in 2's complement
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 180
    assert not cpu.p.zero
    assert cpu.p.negative

    initial_pc = cpu.pc
    cpu.y = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.TAY, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.a = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.a = 42
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 42
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.a = 180  # -76 in 2's complement
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 180
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.INX, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.x = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 1
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 0xF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0x10
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 0xFF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0
    assert cpu.p.zero
    assert not cpu.p.negative
    initial_pc = cpu.pc
    cpu.x = 0x7F
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0x80
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.INY, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.y = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 1
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.y = 0xF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0x10
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.y = 0xFF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0
    assert cpu.p.zero
    assert not cpu.p.negative
    initial_pc = cpu.pc
    cpu.y = 0x7F
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0x80
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.DEX, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.x = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0xFF
    assert not cpu.p.zero
    assert cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 1
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 0xF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0xE
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 0xFF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0xFE
    assert not cpu.p.zero
    assert cpu.p.negative

    initial_pc = cpu.pc
    cpu.x = 0x80
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0x7F
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.DEY, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.y = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0xFF
    assert not cpu.p.zero
    assert cpu.p.negative

    initial_pc = cpu.pc
    cpu.y = 1
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.y = 0xF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0xE
    assert not cpu.p.zero
    assert not cpu.p.negative

    initial_pc = cpu.pc
    cpu.y = 0xFF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0xFE
    assert not cpu.p.zero
    assert cpu.p.negative

    initial_pc = cpu.pc
    cpu.y = 0x80
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 0x7F
    assert not cpu.p.zero
    assert not cpu.p.negative


def test_stack_instructions(system: CPU):
    cpu = system

    ins = Instruction(op=Operation.TXS, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.x = 0x80
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.s == 0x80
    ins = Instruction(op=Operation.TSX, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.s = 0xFF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0xFF

    ins = Instruction(op=Operation.PHA, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.a = 0x42
    cpu.s = 0xFF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.s == 0xFE
    assert cpu.memory[0x100 + cpu.s + 1] == 0x42

    ins = Instruction(op=Operation.PLA, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.a = 0
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.s == 0xFF
    assert cpu.a == 0x42

    ins = Instruction(op=Operation.PHP, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.p._set_flags(0b1011_1101)
    cpu.s = 0xFF
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.s == 0xFE
    assert cpu.memory[0x100 + cpu.s + 1] == 0b1011_1101  # PHP sets the virtual "b" flag aka bit 4

    ins = Instruction(op=Operation.PLP, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.s == 0xFF
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.interrupt_disable
    assert cpu.p.decimal
    assert not cpu.p.overflow
    assert cpu.p.negative


def test_status_register_instructions(system: CPU):
    cpu = system
    ins = Instruction(op=Operation.CLC, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.p.carry = True
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.carry
    ins = Instruction(op=Operation.CLI, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.p.interrupt_disable = True
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.interrupt_disable
    ins = Instruction(op=Operation.CLV, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.p.overflow = True
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.overflow
    ins = Instruction(op=Operation.CLD, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.p.decimal = True
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.decimal
    ins = Instruction(op=Operation.SEC, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.carry
    ins = Instruction(op=Operation.SEI, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.p.interrupt_disable = False
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.interrupt_disable
    ins = Instruction(op=Operation.SED, mode=AddressMode.Implicit)
    initial_pc = cpu.pc
    cpu.p.decimal = False
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.decimal


def test_arithmetic_instructions(system: CPU):
    cpu = system
    # +40 + +2
    ins = Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=2)
    cpu.a = 40
    cpu.execute_instruction(Instruction(op=Operation.CLC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 42
    assert not cpu.p.carry
    assert not cpu.p.overflow
    assert not cpu.p.negative
    # +40 + +2 + Carry
    ins = Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=2)
    cpu.a = 40
    cpu.execute_instruction(Instruction(op=Operation.SEC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 43
    assert not cpu.p.carry
    assert not cpu.p.overflow
    assert not cpu.p.negative
    assert not cpu.p.zero
    # -1 + +1
    ins = Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=1)
    cpu.a = 0xFF
    cpu.execute_instruction(Instruction(op=Operation.CLC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.overflow
    assert not cpu.p.negative
    # -1 + +2
    ins = Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=2)
    cpu.a = 0xFF
    cpu.execute_instruction(Instruction(op=Operation.CLC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 1
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.overflow
    assert not cpu.p.negative
    # -16 + +10
    ins = Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=0xA)
    cpu.a = 0xF0
    cpu.execute_instruction(Instruction(op=Operation.CLC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFA
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.overflow
    assert cpu.p.negative
    # +127 + +1 > max positive (127) -> overflow
    ins = Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=1)
    cpu.a = 0x7F
    cpu.execute_instruction(Instruction(op=Operation.CLC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0x80
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.overflow
    assert cpu.p.negative
    # -1 + +1
    ins = Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=0xFF)
    cpu.a = 1
    cpu.execute_instruction(Instruction(op=Operation.CLC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.overflow
    assert not cpu.p.negative
    # -127 + -127 == -127 - 127 -> smaller then min negative(-128) -> overflow
    # unsigned addition: 129 + 129 bigger then max byte (255) -> carry
    ins = Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=0x81)
    cpu.a = 0x81
    cpu.execute_instruction(Instruction(op=Operation.CLC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 2
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.overflow
    assert not cpu.p.negative
    # 2 - 1, carry set -> +2 + -1 + ^carry -> 2+255 -> wraparound, carry
    ins = Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=1)
    cpu.a = 2
    cpu.execute_instruction(Instruction(op=Operation.SEC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 1
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.overflow
    assert not cpu.p.negative
    # 2 - 1, carry clear -> +2 + -1 +^carry(0) -> +2 + 255 + 1 -> wraparound,carry
    ins = Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=1)
    cpu.a = 2
    cpu.execute_instruction(Instruction(op=Operation.CLC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.overflow
    assert not cpu.p.negative
    # 1-1, carry set -> +1 + -1 + ^carry(1) -> 1 + 255 + 0 -> wraparound,carry
    ins = Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=1)
    cpu.a = 1
    cpu.execute_instruction(Instruction(op=Operation.SEC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.overflow
    assert not cpu.p.negative
    # 1-2, c(1) -> +1 + -2 + 0 -> 1 + 254 -> 255 -> no wraparound
    ins = Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=2)
    cpu.a = 1
    cpu.execute_instruction(Instruction(op=Operation.SEC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFF
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.overflow
    assert cpu.p.negative
    # -1-1, c(1) -> -1 + +1 + 0 -> 255+1 -> wraparound,carry
    ins = Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=1)
    cpu.a = 0xFF
    cpu.execute_instruction(Instruction(op=Operation.SEC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFE
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.overflow
    assert cpu.p.negative
    # -128-1,c(1) -> -128 + -1 + 0 -> 128+255 -> wraparound,carry result less the min negative(-128), overflow
    ins = Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=1)
    cpu.a = 0x80
    cpu.execute_instruction(Instruction(op=Operation.SEC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0x7F
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.overflow
    assert not cpu.p.negative

    ins = Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=0)
    cpu.a = 0x20
    cpu.execute_instruction(Instruction(op=Operation.SEC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0x20
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.overflow
    assert not cpu.p.negative

    ins = Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=0)
    cpu.a = 0x0
    cpu.execute_instruction(Instruction(op=Operation.SEC, mode=AddressMode.Implicit))
    cpu.execute_instruction(Instruction(op=Operation.CLV, mode=AddressMode.Implicit))
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0x0
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.overflow
    assert not cpu.p.negative


# There is no need to test every arithmetic combination with every address mode.
# The code is sufficiently decoupled that I have strong confidence that address modes won't effect the correctness
# of the math calculations or even the operation of the rest of the instructions! We will test the correctness of the address mode
# with ADC and then just use the most convenient address mode to test every other multi address mode instruction


def test_address_modes(full_mem_system: CPU):
    cpu = full_mem_system

    ins = Instruction(op=Operation.ADC, mode=AddressMode.Absolute, operand=0x200)
    cpu.a = 15
    cpu.memory[0x200] = 0xF0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFF

    ins = Instruction(op=Operation.ADC, mode=AddressMode.AbsoluteX, operand=0x200)
    cpu.x = 0x10
    cpu.a = 15
    cpu.memory[0x210] = 0xF0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFF

    ins = Instruction(op=Operation.ADC, mode=AddressMode.AbsoluteY, operand=0x200)
    cpu.y = 0x20
    cpu.a = 14
    cpu.memory[0x220] = 0xF1
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFF

    ins = Instruction(op=Operation.ADC, mode=AddressMode.ZeroPage, operand=0x10)
    cpu.a = 13
    cpu.memory[0x10] = 0xF2
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFF

    ins = Instruction(op=Operation.ADC, mode=AddressMode.ZeroPageX, operand=0x0)
    cpu.x = 0x10
    cpu.a = 15
    cpu.memory[0x10] = 0xF0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFF

    ins = Instruction(op=Operation.LDX, mode=AddressMode.ZeroPageY, operand=0x15)
    cpu.y = 0x5
    cpu.memory[0x1A] = 0x42
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 0x42

    ins = Instruction(op=Operation.ADC, mode=AddressMode.IndirectX, operand=0x10)
    cpu.x = 0x10
    cpu.a = 0x80
    cpu.memory[0x20] = 0x00
    cpu.memory[0x21] = 0xFF
    cpu.memory[0xFF00] = 0x7F
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFF

    # Test zero page address wraparound "feature"
    ins = Instruction(op=Operation.ADC, mode=AddressMode.IndirectX, operand=0xFE)
    cpu.x = 0x1
    cpu.a = 41
    cpu.memory[0xFF] = 0x00
    cpu.memory[0x00] = 0xAA
    cpu.memory[0xAA00] = 1
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 42

    ins = Instruction(op=Operation.ADC, mode=AddressMode.IndirectY, operand=0x60)
    cpu.y = 0xF
    cpu.a = 0x7F
    cpu.memory[0x60] = 0xC0
    cpu.memory[0x61] = 0xD4
    cpu.memory[0xD4CF] = 0x80
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0xFF

    # Test zero page address wraparound "feature"
    ins = Instruction(op=Operation.ADC, mode=AddressMode.IndirectY, operand=0xFF)
    cpu.y = 0xF
    cpu.a = 10
    cpu.memory[0xFF] = 0x40
    cpu.memory[0x00] = 0x70
    cpu.memory[0x704F] = 32
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 42


def test_load_store_instructions(full_mem_system: CPU):
    cpu = full_mem_system

    ins = Instruction(op=Operation.LDA, mode=AddressMode.Immediate, operand=42)
    cpu.a = 0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 42
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.LDA, mode=AddressMode.Immediate, operand=0)
    cpu.a = 42
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.LDA, mode=AddressMode.Immediate, operand=0x86)
    cpu.a = 0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.a == 0x86
    assert not cpu.p.zero
    assert cpu.p.negative

    # The code for handling the flags register is shared for all the LXX instructions so now that we tested it with LDA
    # We will skip it for the other two

    ins = Instruction(op=Operation.LDX, mode=AddressMode.Immediate, operand=1)
    cpu.x = 0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.x == 1

    ins = Instruction(op=Operation.LDY, mode=AddressMode.Immediate, operand=1)
    cpu.y = 0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.y == 1

    # The store addressing mode code is different then the load addressing mode.
    # So we need to test at least one store instruction with all addressing modes.
    ins = Instruction(op=Operation.STA, mode=AddressMode.ZeroPage, operand=0xAC)
    cpu.a = 0x42
    cpu.memory[0xAC] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0xAC] == 0x42

    ins = Instruction(op=Operation.STA, mode=AddressMode.ZeroPageX, operand=0xAC)
    cpu.a = 0x43
    cpu.x = 1
    cpu.memory[0xAD] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0xAD] == 0x43

    ins = Instruction(op=Operation.STA, mode=AddressMode.Absolute, operand=0x4000)
    cpu.a = 0x43
    cpu.x = 1
    cpu.memory[0x4000] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x4000] == 0x43

    ins = Instruction(op=Operation.STA, mode=AddressMode.AbsoluteX, operand=0x4000)
    cpu.a = 0x44
    cpu.x = 0x10
    cpu.memory[0x4010] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x4010] == 0x44

    ins = Instruction(op=Operation.STA, mode=AddressMode.AbsoluteY, operand=0x4000)
    cpu.a = 0x45
    cpu.y = 0x11
    cpu.memory[0x4011] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x4011] == 0x45

    ins = Instruction(op=Operation.STA, mode=AddressMode.IndirectX, operand=0x40)
    cpu.a = 0x46
    cpu.x = 0x10
    cpu.memory[0x50] = 0x12
    cpu.memory[0x51] = 0x40
    cpu.memory[0x4012] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x4012] == 0x46

    ins = Instruction(op=Operation.STA, mode=AddressMode.IndirectY, operand=0x40)
    cpu.a = 0x47
    cpu.y = 0x13
    cpu.memory[0x40] = 0x00
    cpu.memory[0x41] = 0x40
    cpu.memory[0x4013] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x4013] == 0x47

    ins = Instruction(op=Operation.STX, mode=AddressMode.ZeroPage, operand=0xAE)
    cpu.x = 0xFA
    cpu.memory[0xAE] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0xAE] == 0xFA

    # We test STX here again because it's the only instruction with the ZeroPageY addressing mode
    # so we need to test it with this addressing mode to get test coverage for it
    ins = Instruction(op=Operation.STX, mode=AddressMode.ZeroPageY, operand=0x10)
    cpu.x = 0xDD
    cpu.y = 0xB7
    cpu.memory[0xC7] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0xC7] == 0xDD

    ins = Instruction(op=Operation.STY, mode=AddressMode.ZeroPage, operand=0xAF)
    cpu.y = 0xFB
    cpu.memory[0xAF] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0xAF] == 0xFB


def test_inc_dec_instruction(full_mem_system: CPU):
    cpu = full_mem_system

    ins = Instruction(op=Operation.INC, mode=AddressMode.Absolute, operand=0x8000)
    cpu.memory[0x8000] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x8000] == 0x01
    assert not cpu.p.negative
    assert not cpu.p.zero

    ins = Instruction(op=Operation.INC, mode=AddressMode.Absolute, operand=0x8001)
    cpu.memory[0x8001] = 0xFF
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x8001] == 0x0
    assert not cpu.p.negative
    assert cpu.p.zero

    ins = Instruction(op=Operation.DEC, mode=AddressMode.Absolute, operand=0x8002)
    cpu.memory[0x8002] = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x8002] == 0xFF
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.DEC, mode=AddressMode.Absolute, operand=0x8003)
    cpu.memory[0x8003] = 0x1
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.memory[0x8003] == 0x0
    assert cpu.p.zero
    assert not cpu.p.negative


def test_compare_instructions(system: CPU):
    cpu = system

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x69)
    cpu.a = 0x70
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x70)
    cpu.a = 0x69
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x70)
    cpu.a = 0x70
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x0)
    cpu.a = 0x0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x90)
    cpu.a = 0x91
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x91)
    cpu.a = 0x90
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x9)
    cpu.a = 0x90
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x90)
    cpu.a = 0x9
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x70)
    cpu.a = 0x69
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.CPX, mode=AddressMode.Immediate, operand=0x70)
    cpu.x = 0x69
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.CPY, mode=AddressMode.Immediate, operand=0x70)
    cpu.y = 0x70
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert (cpu.pc - initial_pc) == ins.size
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.negative


def test_bit_shift_instructions(system: CPU):
    cpu = system

    ins = Instruction(op=Operation.ASL, mode=AddressMode.Implicit)
    cpu.a = 0x01
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x02
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ASL, mode=AddressMode.Implicit)
    cpu.a = 0xFF
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0xFE
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ASL, mode=AddressMode.Implicit)
    cpu.a = 0xC0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x80
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ASL, mode=AddressMode.Implicit)
    cpu.a = 0x80
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x00
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.negative

    # We need to test a non implicit address mode
    ins = Instruction(op=Operation.ASL, mode=AddressMode.Absolute, operand=0x3FF)
    cpu.memory[0x3FF] = 0x1
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.memory[0x3FF] == 0x02
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.LSR, mode=AddressMode.Implicit)
    cpu.a = 0x01
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x00
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.LSR, mode=AddressMode.Implicit)
    cpu.a = 0xFF
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x7F
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.LSR, mode=AddressMode.Implicit)
    cpu.a = 0xC0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x60
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.LSR, mode=AddressMode.Implicit)
    cpu.a = 0x80
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x40
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ROL, mode=AddressMode.Implicit)
    cpu.p.carry = False
    cpu.a = 0x01
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x02
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ROL, mode=AddressMode.Implicit)
    cpu.p.carry = False
    cpu.a = 0xFF
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0xFE
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ROL, mode=AddressMode.Implicit)
    cpu.p.carry = False
    cpu.a = 0xC0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x80
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ROL, mode=AddressMode.Implicit)
    cpu.p.carry = False
    cpu.a = 0x80
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x00
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ROL, mode=AddressMode.Implicit)
    cpu.p.carry = True
    cpu.a = 0xFF
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0xFF
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ROL, mode=AddressMode.Implicit)
    cpu.p.carry = True
    cpu.a = 0xC0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x81
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ROL, mode=AddressMode.Implicit)
    cpu.p.carry = True
    cpu.a = 0x80
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x01
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ROR, mode=AddressMode.Implicit)
    cpu.p.carry = False
    cpu.a = 0x01
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x00
    assert cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ROR, mode=AddressMode.Implicit)
    cpu.p.carry = False
    cpu.a = 0xFF
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x7F
    assert cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ROR, mode=AddressMode.Implicit)
    cpu.p.carry = False
    cpu.a = 0xC0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x60
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ROR, mode=AddressMode.Implicit)
    cpu.p.carry = False
    cpu.a = 0x80
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0x40
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ROR, mode=AddressMode.Implicit)
    cpu.p.carry = True
    cpu.a = 0xFF
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0xFF
    assert cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ROR, mode=AddressMode.Implicit)
    cpu.p.carry = True
    cpu.a = 0xC0
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0xE0
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ROR, mode=AddressMode.Implicit)
    cpu.p.carry = True
    cpu.a = 0x80
    initial_pc = cpu.pc
    cpu.execute_instruction(ins)
    assert cpu.a == 0xC0
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.negative


def test_bitwise_instructions(system: CPU):
    cpu = system

    ins = Instruction(op=Operation.AND, mode=AddressMode.Immediate, operand=0x1)
    initial_pc = cpu.pc
    cpu.a = 0x1
    cpu.execute_instruction(ins)
    assert cpu.a == 0x01
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.AND, mode=AddressMode.Immediate, operand=0x0)
    initial_pc = cpu.pc
    cpu.a = 0x0
    cpu.execute_instruction(ins)
    assert cpu.a == 0x0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.AND, mode=AddressMode.Immediate, operand=0x1)
    initial_pc = cpu.pc
    cpu.a = 0x0
    cpu.execute_instruction(ins)
    assert cpu.a == 0x0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.AND, mode=AddressMode.Immediate, operand=0x0)
    initial_pc = cpu.pc
    cpu.a = 0x1
    cpu.execute_instruction(ins)
    assert cpu.a == 0x0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.AND, mode=AddressMode.Immediate, operand=0xF)
    initial_pc = cpu.pc
    cpu.a = 0xF0
    cpu.execute_instruction(ins)
    assert cpu.a == 0x00
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.AND, mode=AddressMode.Immediate, operand=0xF0)
    initial_pc = cpu.pc
    cpu.a = 0xFF
    cpu.execute_instruction(ins)
    assert cpu.a == 0xF0
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ORA, mode=AddressMode.Immediate, operand=0x1)
    initial_pc = cpu.pc
    cpu.a = 0x1
    cpu.execute_instruction(ins)
    assert cpu.a == 0x01
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ORA, mode=AddressMode.Immediate, operand=0x0)
    initial_pc = cpu.pc
    cpu.a = 0x0
    cpu.execute_instruction(ins)
    assert cpu.a == 0x0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ORA, mode=AddressMode.Immediate, operand=0x1)
    initial_pc = cpu.pc
    cpu.a = 0x0
    cpu.execute_instruction(ins)
    assert cpu.a == 0x1
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ORA, mode=AddressMode.Immediate, operand=0x0)
    initial_pc = cpu.pc
    cpu.a = 0x1
    cpu.execute_instruction(ins)
    assert cpu.a == 0x1
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.ORA, mode=AddressMode.Immediate, operand=0xF)
    initial_pc = cpu.pc
    cpu.a = 0xF0
    cpu.execute_instruction(ins)
    assert cpu.a == 0xFF
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.ORA, mode=AddressMode.Immediate, operand=0xF0)
    initial_pc = cpu.pc
    cpu.a = 0xFF
    cpu.execute_instruction(ins)
    assert cpu.a == 0xFF
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.EOR, mode=AddressMode.Immediate, operand=0x1)
    initial_pc = cpu.pc
    cpu.a = 0x1
    cpu.execute_instruction(ins)
    assert cpu.a == 0x00
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.EOR, mode=AddressMode.Immediate, operand=0x0)
    initial_pc = cpu.pc
    cpu.a = 0x0
    cpu.execute_instruction(ins)
    assert cpu.a == 0x0
    assert cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.EOR, mode=AddressMode.Immediate, operand=0x1)
    initial_pc = cpu.pc
    cpu.a = 0x0
    cpu.execute_instruction(ins)
    assert cpu.a == 0x1
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.EOR, mode=AddressMode.Immediate, operand=0x0)
    initial_pc = cpu.pc
    cpu.a = 0x1
    cpu.execute_instruction(ins)
    assert cpu.a == 0x1
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.EOR, mode=AddressMode.Immediate, operand=0xF)
    initial_pc = cpu.pc
    cpu.a = 0xF0
    cpu.execute_instruction(ins)
    assert cpu.a == 0xFF
    assert not cpu.p.zero
    assert cpu.p.negative

    ins = Instruction(op=Operation.EOR, mode=AddressMode.Immediate, operand=0xF0)
    initial_pc = cpu.pc
    cpu.a = 0xFF
    cpu.execute_instruction(ins)
    assert cpu.a == 0x0F
    assert not cpu.p.zero
    assert not cpu.p.negative

    ins = Instruction(op=Operation.BIT, mode=AddressMode.ZeroPage, operand=0xA)
    cpu.memory[0xA] = 0x0F
    initial_pc = cpu.pc
    cpu.a = 0xF0
    cpu.execute_instruction(ins)
    assert cpu.a == 0xF0
    assert cpu.p.zero
    assert not cpu.p.negative
    assert not cpu.p.overflow

    ins = Instruction(op=Operation.BIT, mode=AddressMode.ZeroPage, operand=0xA)
    cpu.memory[0xA] = 0xBF
    initial_pc = cpu.pc
    cpu.a = 0x40
    cpu.execute_instruction(ins)
    assert cpu.a == 0x40
    assert cpu.p.zero
    assert cpu.p.negative
    assert not cpu.p.overflow

    ins = Instruction(op=Operation.BIT, mode=AddressMode.ZeroPage, operand=0xA)
    cpu.memory[0xA] = 0x4A
    initial_pc = cpu.pc
    cpu.a = 0x42
    cpu.execute_instruction(ins)
    assert cpu.a == 0x42
    assert not cpu.p.zero
    assert not cpu.p.negative
    assert cpu.p.overflow


def test_branch_instructions(system: CPU):
    cpu = system

    ins = Instruction(op=Operation.BCC, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BCC, mode=AddressMode.Relative, operand=0xF0)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 - 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BCC, mode=AddressMode.Relative, operand=0xF0)
    cpu.pc = 0x00
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 - 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BCC, mode=AddressMode.Relative, operand=0xF1)
    cpu.pc = 0x00
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 - 0xF) & 0xFFFF

    ins = Instruction(op=Operation.BCC, mode=AddressMode.Relative, operand=0xF2)
    cpu.pc = 0x00
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 - 0xE) & 0xFFFF

    ins = Instruction(op=Operation.BCC, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0xFFFF
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BCC, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0xFFFC
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BCC, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.carry = True
    cpu.execute_instruction(ins)
    assert cpu.pc == initial_pc + 2

    ins = Instruction(op=Operation.BCS, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.carry = True
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BCS, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.carry = False
    cpu.execute_instruction(ins)
    assert cpu.pc == initial_pc + 2

    ins = Instruction(op=Operation.BEQ, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.zero = True
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BEQ, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.zero = False
    cpu.execute_instruction(ins)
    assert cpu.pc == initial_pc + 2

    ins = Instruction(op=Operation.BNE, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.zero = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BNE, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.zero = True
    cpu.execute_instruction(ins)
    assert cpu.pc == initial_pc + 2

    ins = Instruction(op=Operation.BMI, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.negative = True
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BMI, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.negative = False
    cpu.execute_instruction(ins)
    assert cpu.pc == initial_pc + 2

    ins = Instruction(op=Operation.BPL, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.negative = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BPL, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.negative = True
    cpu.execute_instruction(ins)
    assert cpu.pc == initial_pc + 2

    ins = Instruction(op=Operation.BVC, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.overflow = False
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BVC, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.overflow = True
    cpu.execute_instruction(ins)
    assert cpu.pc == initial_pc + 2

    ins = Instruction(op=Operation.BVS, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.overflow = True
    cpu.execute_instruction(ins)
    assert cpu.pc == (initial_pc + 2 + 0x10) & 0xFFFF

    ins = Instruction(op=Operation.BVS, mode=AddressMode.Relative, operand=0x10)
    cpu.pc = 0x10
    initial_pc = cpu.pc
    cpu.p.overflow = False
    cpu.execute_instruction(ins)
    assert cpu.pc == initial_pc + 2


def test_jump_instructions(full_mem_system: CPU):
    cpu = full_mem_system

    ins = Instruction(op=Operation.JMP, mode=AddressMode.Absolute, operand=0x1010)
    cpu.execute_instruction(ins)
    assert cpu.pc == 0x1010

    ins = Instruction(op=Operation.JMP, mode=AddressMode.Indirect, operand=0x402D)
    cpu.memory[0x402D : 0x402D + 2] = b"\x15\x10"
    cpu.execute_instruction(ins)
    assert cpu.pc == 0x1015

    ins = Instruction(op=Operation.JMP, mode=AddressMode.Indirect, operand=0xFFFF)
    cpu.memory[0xFFFF] = 0x15
    cpu.memory[0xFF00] = 0x10
    cpu.execute_instruction(ins)
    assert cpu.pc == 0x1015

    ins = Instruction(op=Operation.JMP, mode=AddressMode.Indirect, operand=0x04FF)
    cpu.memory[0x04FF] = 0x55
    cpu.memory[0x0400] = 0x42
    cpu.execute_instruction(ins)
    assert cpu.pc == 0x4255

    ins = Instruction(op=Operation.JSR, mode=AddressMode.Absolute, operand=0x2030)
    # Setup the PC, PC == test_value - instruction length + 1 since that (the address of the last byte of the JSR instruction)
    # is what's get pushed on the stack
    cpu.pc = 0xDEAD - ins.size + 1
    cpu.s = 0xA0
    cpu.execute_instruction(ins)
    assert cpu.pc == 0x2030
    assert cpu.s == 0xA2
    assert cpu.memory[0x100 | cpu.s - 1] == 0xAD
    assert cpu.memory[0x100 | cpu.s - 2] == 0xDE

    ins = Instruction(op=Operation.RTS, mode=AddressMode.Implicit)
    cpu.s = 0xFD
    cpu.memory[0x1FE:0x200] = b"\x41\x43"
    cpu.execute_instruction(ins)
    assert cpu.pc == 0x4342
    assert cpu.s == 0xFF


def test_brk_instruction(system: CPU):
    cpu = system

    ins = Instruction(op=Operation.BRK, mode=AddressMode.Implicit)
    cpu.pc = 0xDEED
    with pytest.raises(CPUTrap):
        cpu.execute_instruction(ins)

    assert cpu.pc == 0xDEEE
    assert cpu.p.interrupt_disable
    stored_flags = cpu.memory[0x100 | cpu.s + 1]
    low_byte = cpu.memory[0x100 | cpu.s + 2]
    high_byte = cpu.memory[0x100 | cpu.s + 3]
    return_address = high_byte << 8 | low_byte
    assert return_address == 0xDEEF
    assert bool(stored_flags & (1 << 4))  # Check "B" flag


def test_rti_instruction(system: CPU):
    cpu = system

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x00\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert not cpu.p.decimal
    assert not cpu.p.interrupt_disable
    assert not cpu.p.negative
    assert not cpu.p.zero
    assert not cpu.p.overflow

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x01\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert cpu.p.carry
    assert not cpu.p.decimal
    assert not cpu.p.interrupt_disable
    assert not cpu.p.negative
    assert not cpu.p.zero
    assert not cpu.p.overflow

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x80\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert not cpu.p.decimal
    assert not cpu.p.interrupt_disable
    assert cpu.p.negative
    assert not cpu.p.zero
    assert not cpu.p.overflow

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x02\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert cpu.p.zero
    assert not cpu.p.interrupt_disable
    assert not cpu.p.decimal
    assert not cpu.p.overflow
    assert not cpu.p.negative

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x04\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert cpu.p.interrupt_disable
    assert not cpu.p.decimal
    assert not cpu.p.overflow
    assert not cpu.p.negative

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x08\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.interrupt_disable
    assert cpu.p.decimal
    assert not cpu.p.overflow
    assert not cpu.p.negative

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x10\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.interrupt_disable
    assert not cpu.p.decimal
    assert not cpu.p.overflow
    assert not cpu.p.negative

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x20\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.interrupt_disable
    assert not cpu.p.decimal
    assert not cpu.p.overflow
    assert not cpu.p.negative

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x40\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.interrupt_disable
    assert not cpu.p.decimal
    assert cpu.p.overflow
    assert not cpu.p.negative

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\x80\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert not cpu.p.carry
    assert not cpu.p.zero
    assert not cpu.p.interrupt_disable
    assert not cpu.p.decimal
    assert not cpu.p.overflow
    assert cpu.p.negative

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.pc = 0x0
    cpu.s = 0xDF
    cpu.memory[0x1E0:0x1E3] = b"\xff\x45\x46"
    cpu.execute_instruction(ins)
    assert cpu.s == 0xE2
    assert cpu.pc == 0x4645
    assert cpu.p.carry
    assert cpu.p.zero
    assert cpu.p.interrupt_disable
    assert cpu.p.decimal
    assert cpu.p.overflow
    assert cpu.p.negative

    cpu.pc = 0x0
    intial_pc = cpu.pc
    cpu.s = 0x40
    initial_s = cpu.s
    cpu.p.carry = True
    cpu.p.zero = True
    cpu.p.interrupt_disable = True
    cpu.p.decimal = True
    cpu.p.overflow = True
    cpu.p.negative = True

    ins = Instruction(op=Operation.BRK, mode=AddressMode.Implicit)
    with pytest.raises(CPUTrap):
        cpu.execute_instruction(ins)
    assert cpu.s == initial_s - 3

    instructions = (
        Instruction(op=Operation.CLC, mode=AddressMode.Implicit),
        Instruction(
            op=Operation.LDA, mode=AddressMode.Immediate, operand=0x1
        ),  # clears both zero and negative flags (which can't be set at the same time in a real 6502)
        Instruction(op=Operation.CLI, mode=AddressMode.Implicit),
        Instruction(op=Operation.CLD, mode=AddressMode.Implicit),
        Instruction(op=Operation.CLV, mode=AddressMode.Implicit),
    )
    for ins in instructions:
        cpu.execute_instruction(ins)
    assert cpu.p.carry == False
    assert cpu.p.zero == False
    assert cpu.p.interrupt_disable == False
    assert cpu.p.decimal == False
    assert cpu.p.overflow == False
    assert cpu.p.negative == False
    assert not cpu.pc == intial_pc + 2

    ins = Instruction(op=Operation.RTI, mode=AddressMode.Implicit)
    cpu.execute_instruction(ins)

    assert cpu.p.carry == True
    assert cpu.p.zero == True
    assert cpu.p.interrupt_disable == True
    assert cpu.p.decimal == True
    assert cpu.p.overflow == True
    assert cpu.p.negative == True

    assert cpu.pc == intial_pc + 2
    assert cpu.s == initial_s
