"""
This module handles 6502 assembly parsing and machine code decoding/encoding.

Classes:
    Operation - An enum that represents all assembly mnemonics
    AddressMode - An enum that represents all operand address modes
    Instruction - A class to represent an assembly instruction
"""

from enum import Enum, auto
from functools import cached_property
from typing import NamedTuple

from memory import MemoryMapView


class EncodingError(Exception):
    """Raise when Instruction object isn't a valid instruction."""

    def __init__(self, message: str, instruction: "Instruction"):
        """Add instruction state to error message."""
        message = f"{message}:\n{instruction}"
        super().__init__(message)


class DecodingError(Exception):
    """Raise when an opcode isn't a valid instruction."""


class Operation(Enum):
    """An enum to represent all 6502 assembly mnemonics."""

    # If you change this, note that the instruction dispatch code in cpu.py implicitly depends on this.
    # Make sure to initialize the operation dispatch array correctly (increase the size for the "dummy" elements),
    # if you change the starting value here.
    ADC = 0
    AND = auto()
    ASL = auto()
    BCC = auto()
    BCS = auto()
    BEQ = auto()
    BIT = auto()
    BMI = auto()
    BNE = auto()
    BPL = auto()
    BRK = auto()
    BVC = auto()
    BVS = auto()
    CLC = auto()
    CLD = auto()
    CLI = auto()
    CLV = auto()
    CMP = auto()
    CPX = auto()
    CPY = auto()
    DEC = auto()
    DEX = auto()
    DEY = auto()
    EOR = auto()
    INC = auto()
    INX = auto()
    INY = auto()
    JMP = auto()
    JSR = auto()
    LDA = auto()
    LDX = auto()
    LDY = auto()
    LSR = auto()
    NOP = auto()
    ORA = auto()
    PHA = auto()
    PHP = auto()
    PLA = auto()
    PLP = auto()
    ROL = auto()
    ROR = auto()
    RTI = auto()
    RTS = auto()
    SBC = auto()
    SEC = auto()
    SED = auto()
    SEI = auto()
    STA = auto()
    STX = auto()
    STY = auto()
    TAX = auto()
    TAY = auto()
    TSX = auto()
    TXA = auto()
    TXS = auto()
    TYA = auto()


class AddressMode(Enum):
    """An enum to represent assembly address modes."""

    # Same thing as the Operation Enum, if you change the starting value here you must adjust the CPU._address_mode_dispatch
    # Init code in cpu.py
    Implicit = 0
    Immediate = auto()
    Relative = auto()
    ZeroPage = auto()
    ZeroPageY = auto()
    ZeroPageX = auto()
    Absolute = auto()
    AbsoluteX = auto()
    AbsoluteY = auto()
    Indirect = auto()
    IndirectX = auto()
    IndirectY = auto()


class Instruction:
    """
    This class models a 6502 assembly instruction.

    Attributes:
        operation - The instruction's operation mnemonic, this is not the machine code opcode! this corresponds to the assembly command (LDA,ADC,...)
        mode - The operand's addressing mode
        operand - The operand's value
        machine_code - The raw machine code of the instructions as a 'bytes' object
        size - the size (in bytes) of the instructions raw machine code
        opcode - The actual raw machine code opcode (the first byte from the 'machine_code' attribute)

    """

    __match_args__ = ("operation", "mode", "operand", "op_code")

    def __init__(self, op: Operation, mode: AddressMode, operand: int | None = None):
        """Initialize the passed in attributes and then the derived attributes."""
        self._operation = op
        self._mode = mode
        self._operand = operand

    def _encode(self) -> bytes:
        try:
            opcode = next(opcode for (opcode, isa_entry) in _isa.opcode_index[self.operation] if isa_entry.mode == self.mode)
        except StopIteration as si:
            raise EncodingError("Address mode is invalid for this operation", self) from si

        match self.mode:
            case AddressMode.Implicit:
                if self.operand is not None:
                    raise EncodingError("Operand not allowed for implicit address mode instructions", self)

                return bytes((opcode,))

            case AddressMode.Absolute | AddressMode.AbsoluteX | AddressMode.AbsoluteY | AddressMode.Indirect:
                if self.operand is None:
                    raise EncodingError("Operand is required for this instruction", self)
                if self.operand > 2**16 - 1:
                    raise EncodingError("Operand is to big for this instruction", self)

                return bytes((opcode, self.operand & 0x00FF, self.operand >> 8))

            case _:
                if self.operand is None:
                    raise EncodingError("Operand is required for this instruction", self)
                if self.operand > 2**8 - 1:
                    raise EncodingError("Operand is to big for this instruction", self)

                return bytes((opcode, self.operand))

    @staticmethod
    def decode(i: bytes | bytearray | MemoryMapView) -> "Instruction":
        """Decode the raw machine code and return an Instruction object, this method only decodes a single instruction from the bytestream."""
        try:
            opcode = i[0]
            isa_entry = _isa[opcode]
        except IndexError as e:
            raise RuntimeError("Can't decode empty byte sequence") from e
        except KeyError as e:
            raise DecodingError(f"Opcode: {i[0]:X} is not a valid opcode") from e

        match isa_entry.mode:
            case AddressMode.Implicit:
                operand = None
            case AddressMode.Absolute | AddressMode.AbsoluteX | AddressMode.AbsoluteY | AddressMode.Indirect:
                operand = (i[2] << 8) + i[1]
            case _:
                operand = i[1]

        return Instruction(op=isa_entry.operation, mode=isa_entry.mode, operand=operand)

    @property
    def operation(self) -> Operation:
        """Get operation attribute."""
        return self._operation

    @property
    def mode(self) -> AddressMode:
        """Get mode attribute."""
        return self._mode

    @property
    def operand(self) -> int | None:
        """Get operand attribute."""
        return self._operand

    @operation.setter
    def operation(self, value: Operation) -> None:
        """Set operation attribute."""
        self._operation = value

        self.__dict__.pop("machine_code", None)
        self.__dict__.pop("size", None)
        self.__dict__.pop("opcode", None)

    @mode.setter
    def mode(self, value: AddressMode) -> None:
        """Set mode attribute."""
        self._mode = value

        self.__dict__.pop("machine_code", None)
        self.__dict__.pop("size", None)
        self.__dict__.pop("opcode", None)

    @operand.setter
    def operand(self, value: int | None) -> None:
        """Set operand attribute."""
        self._operand = value

        self.__dict__.pop("machine_code", None)
        self.__dict__.pop("size", None)
        self.__dict__.pop("opcode", None)

    @cached_property
    def machine_code(self) -> bytes:
        """Implement derived machine_code property."""
        return self._encode()

    @cached_property
    def size(self) -> int:
        """Implement derived size property."""
        # return len(self._encode())
        instructions = _isa.opcode_index[self.operation]
        for ins in instructions:
            if ins[1].mode == self.mode:
                return ins[1].size

        raise RuntimeError(f"Invalid address mode for instruction ({self})")

    @cached_property
    def opcode(self) -> int:
        """Implement derived opcode property."""
        return self._encode()[0]

    def __eq__(self, other) -> bool:
        """
        Define equality for this class.

        Simple attribute-wise comparison. Don't bother with derived attributes.
        """
        if not isinstance(other, Instruction):
            return NotImplemented

        return (self.operation == other.operation) and (self.mode == other.mode) and (self.operand == other.operand)

    def __repr__(self) -> str:
        """Provide human readable debug representation."""
        return f"Instruction(op={self.operation}, mode={self.mode}, operand={self.operand})"


class _ISA_entry(NamedTuple):
    operation: Operation
    mode: AddressMode
    size: int


class _ISA:
    def __init__(self):
        self.opcode_map = {
            0x00: _ISA_entry(Operation.BRK, AddressMode.Implicit, 1),
            0x01: _ISA_entry(Operation.ORA, AddressMode.IndirectX, 2),
            0x05: _ISA_entry(Operation.ORA, AddressMode.ZeroPage, 2),
            0x06: _ISA_entry(Operation.ASL, AddressMode.ZeroPage, 2),
            0x08: _ISA_entry(Operation.PHP, AddressMode.Implicit, 1),
            0x09: _ISA_entry(Operation.ORA, AddressMode.Immediate, 2),
            0x11: _ISA_entry(Operation.ORA, AddressMode.IndirectY, 2),
            0x15: _ISA_entry(Operation.ORA, AddressMode.ZeroPageX, 2),
            0x19: _ISA_entry(Operation.ORA, AddressMode.AbsoluteY, 3),
            0x0A: _ISA_entry(Operation.ASL, AddressMode.Implicit, 1),
            0x0D: _ISA_entry(Operation.ORA, AddressMode.Absolute, 3),
            0x1D: _ISA_entry(Operation.ORA, AddressMode.AbsoluteX, 3),
            0x0E: _ISA_entry(Operation.ASL, AddressMode.Absolute, 3),
            0x10: _ISA_entry(Operation.BPL, AddressMode.Relative, 2),
            0x16: _ISA_entry(Operation.ASL, AddressMode.ZeroPageX, 2),
            0x1E: _ISA_entry(Operation.ASL, AddressMode.AbsoluteX, 3),
            0x18: _ISA_entry(Operation.CLC, AddressMode.Implicit, 1),
            0x20: _ISA_entry(Operation.JSR, AddressMode.Absolute, 3),
            0x21: _ISA_entry(Operation.AND, AddressMode.IndirectX, 2),
            0x24: _ISA_entry(Operation.BIT, AddressMode.ZeroPage, 2),
            0x25: _ISA_entry(Operation.AND, AddressMode.ZeroPage, 2),
            0x26: _ISA_entry(Operation.ROL, AddressMode.ZeroPage, 2),
            0x28: _ISA_entry(Operation.PLP, AddressMode.Implicit, 1),
            0x29: _ISA_entry(Operation.AND, AddressMode.Immediate, 2),
            0x2A: _ISA_entry(Operation.ROL, AddressMode.Implicit, 1),
            0x2C: _ISA_entry(Operation.BIT, AddressMode.Absolute, 3),
            0x2D: _ISA_entry(Operation.AND, AddressMode.Absolute, 3),
            0x2E: _ISA_entry(Operation.ROL, AddressMode.Absolute, 3),
            0x30: _ISA_entry(Operation.BMI, AddressMode.Relative, 2),
            0x35: _ISA_entry(Operation.AND, AddressMode.ZeroPageX, 2),
            0x31: _ISA_entry(Operation.AND, AddressMode.IndirectY, 2),
            0x36: _ISA_entry(Operation.ROL, AddressMode.ZeroPageX, 2),
            0x38: _ISA_entry(Operation.SEC, AddressMode.Implicit, 1),
            0x39: _ISA_entry(Operation.AND, AddressMode.AbsoluteY, 3),
            0x3D: _ISA_entry(Operation.AND, AddressMode.AbsoluteX, 3),
            0x3E: _ISA_entry(Operation.ROL, AddressMode.AbsoluteX, 3),
            0x41: _ISA_entry(Operation.EOR, AddressMode.IndirectX, 2),
            0x40: _ISA_entry(Operation.RTI, AddressMode.Implicit, 1),
            0x45: _ISA_entry(Operation.EOR, AddressMode.ZeroPage, 2),
            0x46: _ISA_entry(Operation.LSR, AddressMode.ZeroPage, 2),
            0x48: _ISA_entry(Operation.PHA, AddressMode.Implicit, 1),
            0x49: _ISA_entry(Operation.EOR, AddressMode.Immediate, 2),
            0x4A: _ISA_entry(Operation.LSR, AddressMode.Implicit, 1),
            0x4C: _ISA_entry(Operation.JMP, AddressMode.Absolute, 3),
            0x4D: _ISA_entry(Operation.EOR, AddressMode.Absolute, 3),
            0x4E: _ISA_entry(Operation.LSR, AddressMode.Absolute, 3),
            0x50: _ISA_entry(Operation.BVC, AddressMode.Relative, 2),
            0x51: _ISA_entry(Operation.EOR, AddressMode.IndirectY, 2),
            0x55: _ISA_entry(Operation.EOR, AddressMode.ZeroPageX, 2),
            0x56: _ISA_entry(Operation.LSR, AddressMode.ZeroPageX, 2),
            0x58: _ISA_entry(Operation.CLI, AddressMode.Implicit, 1),
            0x59: _ISA_entry(Operation.EOR, AddressMode.AbsoluteY, 3),
            0x60: _ISA_entry(Operation.RTS, AddressMode.Implicit, 1),
            0x5D: _ISA_entry(Operation.EOR, AddressMode.AbsoluteX, 3),
            0x5E: _ISA_entry(Operation.LSR, AddressMode.AbsoluteX, 3),
            0x61: _ISA_entry(Operation.ADC, AddressMode.IndirectX, 2),
            0x65: _ISA_entry(Operation.ADC, AddressMode.ZeroPage, 2),
            0x66: _ISA_entry(Operation.ROR, AddressMode.ZeroPage, 2),
            0x68: _ISA_entry(Operation.PLA, AddressMode.Implicit, 1),
            0x69: _ISA_entry(Operation.ADC, AddressMode.Immediate, 2),
            0x6A: _ISA_entry(Operation.ROR, AddressMode.Implicit, 1),
            0x6C: _ISA_entry(Operation.JMP, AddressMode.Indirect, 3),
            0x6D: _ISA_entry(Operation.ADC, AddressMode.Absolute, 3),
            0x6E: _ISA_entry(Operation.ROR, AddressMode.Absolute, 3),
            0x70: _ISA_entry(Operation.BVS, AddressMode.Relative, 2),
            0x71: _ISA_entry(Operation.ADC, AddressMode.IndirectY, 2),
            0x75: _ISA_entry(Operation.ADC, AddressMode.ZeroPageX, 2),
            0x76: _ISA_entry(Operation.ROR, AddressMode.ZeroPageX, 2),
            0x78: _ISA_entry(Operation.SEI, AddressMode.Implicit, 1),
            0x79: _ISA_entry(Operation.ADC, AddressMode.AbsoluteY, 3),
            0x7D: _ISA_entry(Operation.ADC, AddressMode.AbsoluteX, 3),
            0x7E: _ISA_entry(Operation.ROR, AddressMode.AbsoluteX, 3),
            0x81: _ISA_entry(Operation.STA, AddressMode.IndirectX, 2),
            0x84: _ISA_entry(Operation.STY, AddressMode.ZeroPage, 2),
            0x85: _ISA_entry(Operation.STA, AddressMode.ZeroPage, 2),
            0x86: _ISA_entry(Operation.STX, AddressMode.ZeroPage, 2),
            0x88: _ISA_entry(Operation.DEY, AddressMode.Implicit, 1),
            0x8A: _ISA_entry(Operation.TXA, AddressMode.Implicit, 1),
            0x8C: _ISA_entry(Operation.STY, AddressMode.Absolute, 3),
            0x8D: _ISA_entry(Operation.STA, AddressMode.Absolute, 3),
            0x8E: _ISA_entry(Operation.STX, AddressMode.Absolute, 3),
            0x98: _ISA_entry(Operation.TYA, AddressMode.Implicit, 1),
            0x90: _ISA_entry(Operation.BCC, AddressMode.Relative, 2),
            0x91: _ISA_entry(Operation.STA, AddressMode.IndirectY, 2),
            0x94: _ISA_entry(Operation.STY, AddressMode.ZeroPageX, 2),
            0x95: _ISA_entry(Operation.STA, AddressMode.ZeroPageX, 2),
            0x96: _ISA_entry(Operation.STX, AddressMode.ZeroPageY, 2),
            0x99: _ISA_entry(Operation.STA, AddressMode.AbsoluteY, 3),
            0x9A: _ISA_entry(Operation.TXS, AddressMode.Implicit, 1),
            0x9D: _ISA_entry(Operation.STA, AddressMode.AbsoluteX, 3),
            0xA0: _ISA_entry(Operation.LDY, AddressMode.Immediate, 2),
            0xA1: _ISA_entry(Operation.LDA, AddressMode.IndirectX, 2),
            0xA2: _ISA_entry(Operation.LDX, AddressMode.Immediate, 2),
            0xA4: _ISA_entry(Operation.LDY, AddressMode.ZeroPage, 2),
            0xA5: _ISA_entry(Operation.LDA, AddressMode.ZeroPage, 2),
            0xA6: _ISA_entry(Operation.LDX, AddressMode.ZeroPage, 2),
            0xA8: _ISA_entry(Operation.TAY, AddressMode.Implicit, 1),
            0xA9: _ISA_entry(Operation.LDA, AddressMode.Immediate, 2),
            0xAA: _ISA_entry(Operation.TAX, AddressMode.Implicit, 1),
            0xAC: _ISA_entry(Operation.LDY, AddressMode.Absolute, 3),
            0xAD: _ISA_entry(Operation.LDA, AddressMode.Absolute, 3),
            0xAE: _ISA_entry(Operation.LDX, AddressMode.Absolute, 3),
            0xB0: _ISA_entry(Operation.BCS, AddressMode.Relative, 2),
            0xB1: _ISA_entry(Operation.LDA, AddressMode.IndirectY, 2),
            0xB4: _ISA_entry(Operation.LDY, AddressMode.ZeroPageX, 2),
            0xB5: _ISA_entry(Operation.LDA, AddressMode.ZeroPageX, 2),
            0xB6: _ISA_entry(Operation.LDX, AddressMode.ZeroPageY, 2),
            0xB8: _ISA_entry(Operation.CLV, AddressMode.Implicit, 1),
            0xB9: _ISA_entry(Operation.LDA, AddressMode.AbsoluteY, 3),
            0xBA: _ISA_entry(Operation.TSX, AddressMode.Implicit, 1),
            0xBC: _ISA_entry(Operation.LDY, AddressMode.AbsoluteX, 3),
            0xBD: _ISA_entry(Operation.LDA, AddressMode.AbsoluteX, 3),
            0xBE: _ISA_entry(Operation.LDX, AddressMode.AbsoluteY, 3),
            0xC0: _ISA_entry(Operation.CPY, AddressMode.Immediate, 2),
            0xC1: _ISA_entry(Operation.CMP, AddressMode.IndirectX, 2),
            0xC4: _ISA_entry(Operation.CPY, AddressMode.ZeroPage, 2),
            0xC5: _ISA_entry(Operation.CMP, AddressMode.ZeroPage, 2),
            0xC6: _ISA_entry(Operation.DEC, AddressMode.ZeroPage, 2),
            0xC8: _ISA_entry(Operation.INY, AddressMode.Implicit, 1),
            0xC9: _ISA_entry(Operation.CMP, AddressMode.Immediate, 2),
            0xCA: _ISA_entry(Operation.DEX, AddressMode.Implicit, 1),
            0xCC: _ISA_entry(Operation.CPY, AddressMode.Absolute, 3),
            0xCD: _ISA_entry(Operation.CMP, AddressMode.Absolute, 3),
            0xCE: _ISA_entry(Operation.DEC, AddressMode.Absolute, 3),
            0xD0: _ISA_entry(Operation.BNE, AddressMode.Relative, 2),
            0xD1: _ISA_entry(Operation.CMP, AddressMode.IndirectY, 2),
            0xD5: _ISA_entry(Operation.CMP, AddressMode.ZeroPageX, 2),
            0xD6: _ISA_entry(Operation.DEC, AddressMode.ZeroPageX, 2),
            0xDD: _ISA_entry(Operation.CMP, AddressMode.AbsoluteX, 3),
            0xDE: _ISA_entry(Operation.DEC, AddressMode.AbsoluteX, 3),
            0xD8: _ISA_entry(Operation.CLD, AddressMode.Implicit, 1),
            0xD9: _ISA_entry(Operation.CMP, AddressMode.AbsoluteY, 3),
            0xE0: _ISA_entry(Operation.CPX, AddressMode.Immediate, 2),
            0xE1: _ISA_entry(Operation.SBC, AddressMode.IndirectX, 2),
            0xE4: _ISA_entry(Operation.CPX, AddressMode.ZeroPage, 2),
            0xE5: _ISA_entry(Operation.SBC, AddressMode.ZeroPage, 2),
            0xE6: _ISA_entry(Operation.INC, AddressMode.ZeroPage, 2),
            0xE8: _ISA_entry(Operation.INX, AddressMode.Implicit, 1),
            0xE9: _ISA_entry(Operation.SBC, AddressMode.Immediate, 2),
            0xEA: _ISA_entry(Operation.NOP, AddressMode.Implicit, 1),
            0xEC: _ISA_entry(Operation.CPX, AddressMode.Absolute, 3),
            0xED: _ISA_entry(Operation.SBC, AddressMode.Absolute, 3),
            0xEE: _ISA_entry(Operation.INC, AddressMode.Absolute, 3),
            0xF0: _ISA_entry(Operation.BEQ, AddressMode.Relative, 2),
            0xF1: _ISA_entry(Operation.SBC, AddressMode.IndirectY, 2),
            0xF5: _ISA_entry(Operation.SBC, AddressMode.ZeroPageX, 2),
            0xF6: _ISA_entry(Operation.INC, AddressMode.ZeroPageX, 2),
            0xF8: _ISA_entry(Operation.SED, AddressMode.Implicit, 1),
            0xF9: _ISA_entry(Operation.SBC, AddressMode.AbsoluteY, 3),
            0xFE: _ISA_entry(Operation.INC, AddressMode.AbsoluteX, 3),
            0xFD: _ISA_entry(Operation.SBC, AddressMode.AbsoluteX, 3),
        }

        self.opcode_index: dict[Operation, list[tuple[int, _ISA_entry]]] = {}

        for operation in Operation:
            self.opcode_index[operation] = []

        for opcode, isa_entry in self.opcode_map.items():
            self.opcode_index[isa_entry.operation].append((opcode, isa_entry))

    def __getitem__(self, key: int) -> _ISA_entry:
        return self.opcode_map[key]


_isa = _ISA()
