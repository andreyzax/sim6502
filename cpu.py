"""
This module implements the 6502 cpu and other program execution logic.

Classes:
    CPUTrap - Exception used for cpu trap conditions
    CPU - Model of the 6502 cpu

Arithmetic & integer representation note:
    We do not use python's arbitrary precision signed ints to *directly* represent the 6502 register values
    instead we keep values in the 8 bit positive range (0-255) and implement two's complement representation on top of it
    so that values in range of 0-127 are "positive" and 128-255 are "negative".
    Our two arithmetic instructions (ADC, SBC) and our status register behave accordingly.

"""

import copy
from dataclasses import dataclass
from typing import Callable

from assembly import AddressMode, Instruction, Operation
from memory import MemoryMap


class CPUTrap(Exception):
    """Raised on cpu traps to break out of the execution loop."""

    def __init__(self, cpu: "CPU"):
        """Pass in the CPU object as the trap context."""
        self.cpu = cpu


class CPU:
    """Emulates the 6502 cpu core."""

    @staticmethod
    def _is_8bit_negative(i: int) -> bool:
        """Check if the number is negative."""
        return bool(i & 0x80)

    @staticmethod
    def _negate_8bit(i: int) -> int:
        """Inverse sign of value."""
        return (~i + 1) & 0xFF

    @staticmethod
    def _sign_extend_16_bit(i: int) -> int:
        """Extend from 8 to 16 bit."""
        if i > 0xFF:
            raise ValueError(f"value {i} is bigger then 255, can't extend values wider then 8 bits")

        return i | 0xFF00 if i & 0x80 else i & 0xFFFF

    def _fetch_16bit(self, address: int) -> int:
        value = self.memory[address + 1 & 0xFFFF]
        value <<= 8
        value |= self.memory[address & 0xFFFF]

        return value

    def _fetch_zero_page_16bit(self, address: int) -> int:
        value = self.memory[address + 1 & 0xFF]
        value <<= 8
        value |= self.memory[address & 0xFF]

        return value

    def _update_flags(self, result: int) -> None:
        """
        Set the status register according to result.

        This is the generic flags handling logic and *not* all instructions use this!
        """
        self.p.negative = self._is_8bit_negative(result)
        self.p.zero = not bool(result)

    def _compare_update_flags(self, result: int) -> None:
        """Update status register after comparison operations."""
        self.p.carry = result > 0xFF
        self.p.zero = (result & 0xFF) == 0
        self.p.negative = self._is_8bit_negative(result)

    def _fetch_indirect(self, pointer: int) -> int:
        address = self._fetch_16bit(pointer)

        return self.memory[address]  # No need for 16 bit guard, _fetch_16bit() is guaranteed to return a 16 bit value

    def _fetch_indirect_zero_page_x(self, base_pointer: int) -> int:
        address = self.memory[(base_pointer + self.x + 1) & 0xFF]
        address <<= 8
        address |= self.memory[(base_pointer + self.x) & 0xFF]
        return self.memory[address & 0xFFFF]

    def _fetch_indirect_zero_page_y(self, base_pointer: int) -> int:
        address = self.memory[base_pointer + 1 & 0xFF]
        address <<= 8
        address |= self.memory[base_pointer & 0xFF]
        address += self.y
        return self.memory[address & 0xFFFF]

    def _fetch_zero_pagex(self, base_address: int) -> int:
        address = (base_address + self.x) & 0xFF
        return self.memory[address]

    def _fetch_zero_pagey(self, base_address: int) -> int:
        address = (base_address + self.y) & 0xFF
        return self.memory[address]

    def _fetch_absolute_x(self, base_address: int) -> int:
        address = (base_address + self.x) & 0xFFFF
        return self.memory[address]

    def _fetch_absolute_y(self, base_address: int) -> int:
        address = (base_address + self.y) & 0xFFFF
        return self.memory[address]

    def _fetch_operand(self, ins: Instruction) -> int:
        if ins.mode == AddressMode.Implicit:
            raise RuntimeError(f"CAn't fetch an operand for Instruction {ins} which is an implicit mode instruction")

        if ins.operand is None:
            raise RuntimeError(f"Instruction {ins} requires an operand")

        if ins.mode == AddressMode.Immediate or ins.mode == AddressMode.Relative:
            return ins.operand
        else:
            return self._address_mode_dispatch[ins.mode](ins.operand)

    def _compute_address(self, ins: Instruction) -> int:
        if ins.operand is None:
            raise RuntimeError(f"Can't compute address for instruction: {ins} without an operand")

        match ins.mode:
            # Indirect and relative addressing modes are not covered here
            # and are handled as a special case by the instructions using them.
            # It's (obviously) impossible to compute the address of implicit or immediate modes

            case AddressMode.Absolute | AddressMode.ZeroPage:
                return ins.operand
            case AddressMode.AbsoluteX:
                return (ins.operand + self.x) & 0xFFFF
            case AddressMode.AbsoluteY:
                return (ins.operand + self.y) & 0xFFFF
            case AddressMode.ZeroPageX:
                return (ins.operand + self.x) & 0xFF
            case AddressMode.ZeroPageY:
                return (ins.operand + self.y) & 0xFF
            case AddressMode.IndirectX:
                return self._fetch_zero_page_16bit(ins.operand + self.x)
            case AddressMode.IndirectY:
                pointer = self._fetch_zero_page_16bit(ins.operand)
                return (pointer + self.y) & 0xFFFF
            case _:
                raise RuntimeError(f"Can't compute address for mode: {ins.mode}")

    def _do_register_instructions(self, ins: Instruction) -> None:

        match ins.operation:
            case Operation.TAX:
                self.x = self.a
                self._update_flags(self.x)
            case Operation.TXA:
                self.a = self.x
                self._update_flags(self.a)
            case Operation.TAY:
                self.y = self.a
                self._update_flags(self.y)
            case Operation.TYA:
                self.a = self.y
                self._update_flags(self.a)
            case Operation.INX:
                self.x = self.x + 1
                self._update_flags(self.x)
            case Operation.INY:
                self.y = self.y + 1
                self._update_flags(self.y)
            case Operation.DEX:
                self.x = self.x - 1
                self._update_flags(self.x)
            case Operation.DEY:
                self.y = self.y - 1
                self._update_flags(self.y)
            case _:
                raise RuntimeError(f"Operation: {ins.operation} is not a valid register operation")

    def _do_stack_instructions(self, ins: Instruction) -> None:
        match ins.operation:
            case Operation.TXS:
                self.s = self.x
            case Operation.TSX:
                self.x = self.s
            case Operation.PHA:
                self.memory[0x100 + self.s] = self.a
                self.s -= 1
            case Operation.PLA:
                self.s += 1
                self.a = self.memory[0x100 + self.s]
            case Operation.PHP:
                flags = self.p._get_flags()
                flags |= 1 << 4  # PHP sets the "b" flag
                self.memory[0x100 + self.s] = flags
                self.s -= 1
            case Operation.PLP:
                self.s += 1
                self.p._set_flags(self.memory[0x100 + self.s])
            case _:
                raise RuntimeError(f"Operation: {ins.operation} is not a valid stack operation")

    def _do_status_register_instructions(self, ins: Instruction) -> None:
        match ins.operation:
            case Operation.CLC:
                self.p.carry = False
            case Operation.CLI:
                self.p.interrupt_disable = False
            case Operation.CLV:
                self.p.overflow = False
            case Operation.CLD:
                self.p.decimal = False
            case Operation.SEC:
                self.p.carry = True
            case Operation.SEI:
                self.p.interrupt_disable = True
            case Operation.SED:
                self.p.decimal = True
            case _:
                raise RuntimeError(f"Operation: {ins.operation} is not a valid status register operation")

    def _do_arithmetic_instructions(self, ins: Instruction) -> None:
        if self.p.decimal:
            raise RuntimeError("Decimal mode arithmetic not implemented")

        operand = self._fetch_operand(ins)

        operand = (~operand & 0xFF) if ins.operation == Operation.SBC else operand
        operand += int(self.p.carry) & 0xFF

        result = self.a + operand

        self.p.negative = self._is_8bit_negative(result)
        self.p.carry = result > 0xFF

        self.p.overflow = False  # Pre-clear the flag to get correct behavior, we want this actively cleared if signed overflow didn't occur
        # not just keep this unchanged
        if (self._is_8bit_negative(self.a) and self._is_8bit_negative(operand)) and not self._is_8bit_negative(result):
            self.p.overflow = True
        if (not self._is_8bit_negative(self.a) and not self._is_8bit_negative(operand)) and self._is_8bit_negative(result):
            self.p.overflow = True

        self.a = result & 0xFF  # Make sure to keep this here *after* the overflow check, we need to use the old value there.

        self.p.zero = self.a == 0  # We check this here against the final result since we need to mask off the value to know if it's zero,
        # doing it here saves us one extra bitmask operation.

    def _do_load_store_instructions(self, ins: Instruction) -> None:
        if ins.operation in (Operation.LDA, Operation.LDX, Operation.LDY):
            operand = self._fetch_operand(ins)

            match ins.operation:
                case Operation.LDA:
                    self.a = operand
                    self._update_flags(self.a)
                case Operation.LDX:
                    self.x = operand
                    self._update_flags(self.x)
                case Operation.LDY:  # pragma: no branch - Outer if protects against fallthrough
                    self.y = operand
                    self._update_flags(self.y)
        else:
            address = self._compute_address(ins)

            match ins.operation:
                case Operation.STA:
                    self.memory[address] = self.a
                case Operation.STX:
                    self.memory[address] = self.x
                case Operation.STY:
                    self.memory[address] = self.y
                case _:
                    raise RuntimeError(f"Operation: {ins.operation} is not a valid load/store operation")

    def _do_mem_inc_dec_instructions(self, ins: Instruction) -> None:
        address = self._compute_address(ins)

        if ins.operation == Operation.INC:
            self.memory[address] = (self.memory[address] + 1) & 0xFF
            self._update_flags(self.memory[address])
        elif ins.operation == Operation.DEC:
            self.memory[address] = (self.memory[address] - 1) & 0xFF
            self._update_flags(self.memory[address])
        else:
            raise RuntimeError(f"Operation: {ins.operation} is not a valid inc/dec operation")

    def _do_compare_instructions(self, ins: Instruction) -> None:
        operand = self._fetch_operand(ins)

        match ins.operation:
            case Operation.CMP:
                register = self.a
            case Operation.CPX:
                register = self.x
            case Operation.CPY:
                register = self.y
            case _:
                raise RuntimeError(f"Operation: {ins.operation} is not a valid compare operation")

        # This is emulating the implicit SBC for comparison instructions. 1's complement the operand
        # (flip the bits) and mask off the high bits to emulate 8 bit math. then add with "carry" set.
        # For comparisons we always add a carry regardless of the actual carry flag. We *dont* mask off the result because,
        # we don't actually save it anywhere so there is no point *and* we actually need to preserve any overflow
        # so we can set the carry flag correctly in `self._compare_update_flags()`
        operand = ~operand & 0xFF
        result = register + operand + 1  # Don't mask off the bits here, we want to preserve any overflow for the flags check

        self._compare_update_flags(result)

    def _do_bit_shift_instructions(self, ins: Instruction) -> None:
        operand = self.a if ins.mode == AddressMode.Implicit else self._fetch_operand(ins)

        match ins.operation:
            case Operation.ASL:
                operand <<= 1
                self.p.carry = bool(operand & 0x100)
                self.p.negative = self._is_8bit_negative(operand)
                operand &= 0xFF
                self.p.zero = operand == 0
            case Operation.LSR:
                self.p.carry = bool(operand & 0x1)  # Check bit 0, which will be the shifted out bit
                operand >>= 1
                self.p.zero = operand == 0
                self.p.negative = self._is_8bit_negative(operand)
            case Operation.ROL:
                new_bit_0 = int(self.p.carry)
                operand <<= 1
                self.p.carry = bool(operand & 0x100)
                operand |= new_bit_0
                self.p.negative = self._is_8bit_negative(operand)
                operand &= 0xFF
                self.p.zero = operand == 0
            case Operation.ROR:
                new_bit_7 = int(self.p.carry) << 7
                self.p.carry = bool(operand & 0x1)
                operand >>= 1
                operand |= new_bit_7
                operand &= 0xFF
                self.p.negative = self._is_8bit_negative(operand)
                self.p.zero = operand == 0
            case _:
                raise RuntimeError(f"Operation: {ins.operation} is not a valid bit shift operation")

        if ins.mode == AddressMode.Implicit:
            self.a = operand
        else:
            address = self._compute_address(ins)
            self.memory[address] = operand & 0xFF

    def _do_bitwise_instructions(self, ins: Instruction) -> None:
        operand = self._fetch_operand(ins)

        match ins.operation:
            case Operation.AND:
                self.a &= operand
            case Operation.ORA:
                self.a |= operand
            case Operation.EOR:
                self.a ^= operand
            case _:
                raise RuntimeError(f"Operation: {ins.operation} is not a valid bitwise operation")

        self._update_flags(self.a)

    def _do_bit_instruction(self, ins: Instruction) -> None:
        if ins.operation != Operation.BIT:
            raise RuntimeError(f"Instruction {ins} is not a BIT instruction")

        operand = self._fetch_operand(ins)

        result = self.a & operand

        self.p.zero = result == 0
        self.p.negative = self._is_8bit_negative(operand)
        self.p.overflow = bool(operand & 0x40)  # copy bit 6 as per documentation

    def _do_branch_instructions(self, ins: Instruction) -> None:
        operand = self._fetch_operand(ins)
        operand = self._sign_extend_16_bit(operand)

        match ins.operation:
            case Operation.BCC:
                if not self.p.carry:
                    self.pc += operand
            case Operation.BCS:
                if self.p.carry:
                    self.pc += operand
            case Operation.BEQ:
                if self.p.zero:
                    self.pc += operand
            case Operation.BNE:
                if not self.p.zero:
                    self.pc += operand
            case Operation.BPL:
                if not self.p.negative:
                    self.pc += operand
            case Operation.BMI:
                if self.p.negative:
                    self.pc += operand
            case Operation.BVC:
                if not self.p.overflow:
                    self.pc += operand
            case Operation.BVS:
                if self.p.overflow:
                    self.pc += operand
            case _:
                raise RuntimeError(f"Operation: {ins.operation} is not a branch operation")

    def _do_jump_instructions(self, ins: Instruction) -> None:
        if ins.operation not in (Operation.JMP, Operation.JSR):
            raise RuntimeError(f"Operation: {ins.operation} is not a jump operation")

        # Usually self._fetch_operand() would check for this but here
        # we can pass in ins.operand directly which could be None
        if not ins.operand:
            raise RuntimeError(f"Instruction {ins} doesn't have an operand, jump instructions require it")

        # Special case addressing mode handling since they work different for jump instructions. We don't want to
        # (fully) dereference the operands. for absolute mode, use it as is (like it's immediate mode).
        # For indirect we dereference the first pointer and then use it as is (as if it's absolute mode).
        # So one less level of indirection then usual.
        #
        # We also need to implement the infamous page crossing bug for indirect mode
        if ins.mode not in (AddressMode.Absolute, AddressMode.Indirect):
            raise RuntimeError(f"Invalid addressing mode for instruction {ins}")

        if ins.mode == AddressMode.Absolute:
            operand = ins.operand
        else:
            if (ins.operand & 0xFF) == 0xFF:
                # Implement the page crossing "feature" in indirect mode
                low_byte = self.memory[ins.operand]
                high_byte = self.memory[ins.operand & 0xFF00]
                operand = (high_byte << 8) | low_byte
            else:
                operand = self._fetch_16bit(ins.operand)

        if ins.operation == Operation.JSR:
            # self.pc - 1 isn't a bug! JSR stores the address *before* the next instruction
            # (the address of it's operand's high byte) and RTS then *increments* the pulled address
            # to correct it and returns to the next instruction.
            self.memory[0x100 + self.s] = (self.pc - 1) >> 8
            self.memory[0x100 + self.s - 1] = (self.pc - 1) & 0xFF
            self.s -= 2

        self.pc = operand

    def _do_rts_instruction(self, ins: Instruction) -> None:
        low_byte = self.memory[0x100 + self.s + 1]
        high_byte = self.memory[0x100 + self.s + 2]
        self.s += 2

        # Add one to "correct" for JSR's quirk of pushing it's own end address instead of pushing
        # the next address to the stack.
        self.pc = ((high_byte << 8) | low_byte) + 1

    def _do_brk_instruction(self, ins: Instruction) -> None:
        """
        Currently BRK is not emulated as a software interrupt as it was on the real hardware.

        Instead it is used as a way to break out of the emulation loop into the hosting context,
        where the emulation state could be examined, modified and continued (or restarted).
        We do conduct the pre-jump "ceremony", pushing the PC and status register (including the B flag)
        and disabling interrupts so our state matches the real hardware. Only the final step of the indirect
        jump via the 0xFFFE vector is avoided, we simply exit the emulation loop instead.
        """
        # While JSR pushes the address before the next instruction, BRK pushes
        # a return address that skips the next byte and unlike RTS the RTI instruction doesn't
        # "correct" it, returning from a BRK handler skips one byte in the instruction stream (which is why
        # many consider this a 2 byte instruction even though it's an implicit mode instruction without any operands).
        #
        # None of this is actually relevant for this implementation since it doesn't actually jump anywhere.
        self.memory[0x100 + self.s] = (self.pc + 1) >> 8
        self.memory[0x100 + self.s - 1] = (self.pc + 1) & 0xFF

        flags = self.p._get_flags()
        flags |= 1 << 4  # BRK sets the "b" flag
        self.memory[0x100 + self.s - 2] = flags
        self.s -= 3
        self.p.interrupt_disable = True

        raise CPUTrap(cpu=self)

    def _do_rti_instruction(self, ins: Instruction) -> None:
        self.p._set_flags(self.memory[0x100 | self.s + 1])
        low_byte = self.memory[0x100 | self.s + 2]
        high_byte = self.memory[0x100 | self.s + 3]
        self.pc = high_byte << 8 | low_byte  # Unlike RTS we don't adjust the return address
        self.s += 3

    @dataclass
    class _StatusRegister:
        carry: bool = False
        zero: bool = False
        interrupt_disable: bool = False
        decimal: bool = False
        overflow: bool = False
        negative: bool = False

        def _set_flags(self, i: int) -> None:
            i &= 0xFF
            self.carry = bool(i & 0b0000_0001)
            self.zero = bool(i & 0b0000_0010)
            self.interrupt_disable = bool(i & 0b0000_0100)
            self.decimal = bool(i & 0b0000_1000)
            # Bits 4 & 5 are not stored in the register
            self.overflow = bool(i & 0b0100_0000)
            self.negative = bool(i & 0b1000_0000)

        def _get_flags(self) -> int:
            res = 0

            res |= int(self.carry)
            res |= int(self.zero) << 1
            res |= int(self.interrupt_disable) << 2
            res |= int(self.decimal) << 3
            res |= 0 << 4  # So called "B" flag, not stored in the register, and actually set by the instruction reading the status register
            # we set it to zero here as a place holder.
            res |= 1 << 5  # bit 5 is not stored in the register and always read as 1 when reading the status register
            res |= int(self.overflow) << 6
            res |= int(self.negative) << 7

            return res

    def reset(self):
        """Reset the cpu state."""
        self._a = self._init_a
        self._x = self._init_x
        self._y = self._init_y
        self._pc = self._init_pc
        self._s = self._init_s
        self.p = copy.copy(self._init_p)

    def __init__(self, memory: MemoryMap, pc: int = 0, s: int = 0xFF):
        """Initialize the cpu state."""
        self._init_a = 0
        self._init_x = 0
        self._init_y = 0
        self._init_pc = pc
        self._init_s = s
        self._init_p = self._StatusRegister()
        self.memory = memory
        self.reset()

        self._instruction_dispatch: dict[Operation, Callable[[Instruction], None]] = {
            Operation.NOP: lambda _: None,
            Operation.TAX: self._do_register_instructions,
            Operation.TXA: self._do_register_instructions,
            Operation.TAY: self._do_register_instructions,
            Operation.TYA: self._do_register_instructions,
            Operation.INX: self._do_register_instructions,
            Operation.INY: self._do_register_instructions,
            Operation.INC: self._do_mem_inc_dec_instructions,
            Operation.DEC: self._do_mem_inc_dec_instructions,
            Operation.DEX: self._do_register_instructions,
            Operation.DEY: self._do_register_instructions,
            Operation.TXS: self._do_stack_instructions,
            Operation.TSX: self._do_stack_instructions,
            Operation.PHA: self._do_stack_instructions,
            Operation.PLA: self._do_stack_instructions,
            Operation.PHP: self._do_stack_instructions,
            Operation.PLP: self._do_stack_instructions,
            Operation.CLC: self._do_status_register_instructions,
            Operation.CLI: self._do_status_register_instructions,
            Operation.CLV: self._do_status_register_instructions,
            Operation.CLD: self._do_status_register_instructions,
            Operation.SEC: self._do_status_register_instructions,
            Operation.SEI: self._do_status_register_instructions,
            Operation.SED: self._do_status_register_instructions,
            Operation.ADC: self._do_arithmetic_instructions,
            Operation.SBC: self._do_arithmetic_instructions,
            Operation.LDA: self._do_load_store_instructions,
            Operation.LDX: self._do_load_store_instructions,
            Operation.LDY: self._do_load_store_instructions,
            Operation.STA: self._do_load_store_instructions,
            Operation.STX: self._do_load_store_instructions,
            Operation.STY: self._do_load_store_instructions,
            Operation.INC: self._do_mem_inc_dec_instructions,
            Operation.DEC: self._do_mem_inc_dec_instructions,
            Operation.CMP: self._do_compare_instructions,
            Operation.CPX: self._do_compare_instructions,
            Operation.CPY: self._do_compare_instructions,
            Operation.ASL: self._do_bit_shift_instructions,
            Operation.LSR: self._do_bit_shift_instructions,
            Operation.ROL: self._do_bit_shift_instructions,
            Operation.ROR: self._do_bit_shift_instructions,
            Operation.AND: self._do_bitwise_instructions,
            Operation.ORA: self._do_bitwise_instructions,
            Operation.EOR: self._do_bitwise_instructions,
            Operation.BIT: self._do_bit_instruction,
            Operation.BCC: self._do_branch_instructions,
            Operation.BCS: self._do_branch_instructions,
            Operation.BEQ: self._do_branch_instructions,
            Operation.BMI: self._do_branch_instructions,
            Operation.BNE: self._do_branch_instructions,
            Operation.BPL: self._do_branch_instructions,
            Operation.BMI: self._do_branch_instructions,
            Operation.BVC: self._do_branch_instructions,
            Operation.BVS: self._do_branch_instructions,
            Operation.JMP: self._do_jump_instructions,
            Operation.JSR: self._do_jump_instructions,
            Operation.RTS: self._do_rts_instruction,
            Operation.BRK: self._do_brk_instruction,
            Operation.RTI: self._do_rti_instruction,
        }

        self._address_mode_dispatch: dict[AddressMode, Callable[[int], int]] = {
            AddressMode.Absolute: lambda address: self.memory[address & 0xFFFF],
            AddressMode.AbsoluteX: self._fetch_absolute_x,
            AddressMode.AbsoluteY: self._fetch_absolute_y,
            AddressMode.ZeroPage: lambda address: self.memory[address & 0xFF],
            AddressMode.ZeroPageX: self._fetch_zero_pagex,
            AddressMode.ZeroPageY: self._fetch_zero_pagey,
            AddressMode.Indirect: self._fetch_indirect,
            AddressMode.IndirectX: self._fetch_indirect_zero_page_x,
            AddressMode.IndirectY: self._fetch_indirect_zero_page_y,
        }

    @property
    def pc(self) -> int:
        """
        PC register getter.

        This is only defined because the setter needs a getter to be defined.
        Otherwise it just returns the internal attribute.
        """
        return self._pc

    @pc.setter
    def pc(self, value: int) -> None:
        """Set PC register, ensures the register is bound to a 16 bit range with wrap around semantics."""
        self._pc = value & 0xFFFF  # Ensure 16 bit wraparound

    @property
    def a(self) -> int:
        """
        A register getter.

        This is only defined because the setter needs a getter to be defined.
        Otherwise it just returns the internal attribute.
        """
        return self._a

    @a.setter
    def a(self, value: int) -> None:
        """Set A register, ensures the register is bound to an 8 bit range with wrap around semantics."""
        self._a = value & 0xFF  # Ensure 8 bit wraparound

    @property
    def x(self) -> int:
        """
        X register getter.

        This is only defined because the setter needs a getter to be defined.
        Otherwise it just returns the internal attribute.
        """
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        """Set X register, ensures the register is bound to an 8 bit range with wrap around semantics."""
        self._x = value & 0xFF  # Ensure 8 bit wraparound

    @property
    def y(self) -> int:
        """
        Y register getter.

        This is only defined because the setter needs a getter to be defined.
        Otherwise it just returns the internal attribute.
        """
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        """Set A register, ensures the register is bound to an 8 bit range with wrap around semantics."""
        self._y = value & 0xFF  # Ensure 8 bit wraparound

    @property
    def s(self) -> int:
        """
        S (stack pointer) register getter.

        This is only defined because the setter needs a getter to be defined.
        Otherwise it just returns the internal attribute.
        """
        return self._s

    @s.setter
    def s(self, value: int) -> None:
        """Set S register, ensures the register is bound to an 8 bit range with wrap around semantics."""
        self._s = value & 0xFF  # Ensure 8 bit wraparound

    def execute_instruction(self, ins: Instruction) -> None:
        """Execute a single instruction. Update registers and memory as per ISA requirements."""
        self.pc += ins.size  # Very important we do this before dispatch to make branches, jumps & JSR work properly
        try:
            self._instruction_dispatch[ins.operation](ins)
        except KeyError as e:
            raise RuntimeError(f"Operation: <{ins.operation}> is not implemented.") from e

    def _decode(self) -> Instruction:
        return Instruction.decode(self.memory[self.pc : self.pc + 3])  # Luckily for us the maximum instruction size on the 6502 is 3 bytes
        # So we feed Instruction.decode() a small 3 element slice that's guarantee to contain the whole instruction, Instruction.decode()
        # will simply ignore any extra bytes if the instruction is less then 3 bytes long

    def step(self) -> None:
        """Execute one instruction from the current PC location and advance the PC to the next instruction."""
        ins = self._decode()
        self.execute_instruction(ins)

    def run(self, trap_handler: Callable[["CPU"]] | None) -> None:
        """Start the cpu's run loop, we only stop due to exceptions."""
        try:
            while True:
                self.step()
        except CPUTrap as ctx:
            if trap_handler is not None:
                trap_handler(ctx.cpu)
            else:
                raise
