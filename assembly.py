"""
This module handles 6502 assembly parsing and machine code decoding/encoding.

Classes:
    Operation - An enum that represents all assembly mnemonics
    AddressMode - An enum that represents all operand address modes
    Instruction - A class to represent an assembly instruction
"""

from enum import Enum, auto
from typing import NamedTuple


class EncodingError(Exception):
    """Raise when Instruction object isn't a valid instruction."""

    def __init__(self, message: str, instruction: "Instruction"):
        """Add instruction state to error message."""
        message = f"{message}:\n{instruction}"
        super().__init__(message)


class Operation(Enum):
    """An enum to represent all 6502 assembly mnemonics."""

    ADC = auto()
    BEQ = auto()
    BNE = auto()
    BRK = auto()
    CLC = auto()
    CMP = auto()
    DEC = auto()
    DEX = auto()
    DEY = auto()
    INC = auto()
    INX = auto()
    INY = auto()
    JMP = auto()
    LDA = auto()
    LDX = auto()
    LDY = auto()
    NOP = auto()
    PHA = auto()
    PLA = auto()
    SBC = auto()
    SEC = auto()
    STA = auto()
    STX = auto()
    STY = auto()


class AddressMode(Enum):
    """An enum to represent assembly address modes."""

    Implicit = auto()
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
        self.operation = op
        self.mode = mode
        self.operand = operand

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

                return bytes((opcode, self.operand >> 8, self.operand & 0x00FF))

            case _:
                if self.operand is None:
                    raise EncodingError("Operand is required for this instruction", self)
                if self.operand > 2**8 - 1:
                    raise EncodingError("Operand is to big for this instruction", self)

                return bytes((opcode, self.operand))

    @staticmethod
    def decode(i: bytes | bytearray | memoryview) -> "Instruction":
        """Decode the raw machine code and return an Instruction object, this method only decodes a single instruction from the bytestream."""
        opcode = i[0]
        isa_entry = _isa[opcode]

        match isa_entry.mode:
            case AddressMode.Implicit:
                operand = None
            case AddressMode.Absolute | AddressMode.AbsoluteX | AddressMode.AbsoluteY | AddressMode.Indirect:
                operand = (i[2] << 8) + i[1]
            case _:
                operand = i[1]

        return Instruction(op=isa_entry.operation, mode=isa_entry.mode, operand=operand)

    @property
    def machine_code(self) -> bytes:
        """Implement derived machine_code property."""
        return self._encode()

    @property
    def size(self) -> int:
        """Implement derived size property."""
        return len(self._encode())

    @property
    def opcode(self) -> int:
        """Implement derived opcode property."""
        return self._encode()[0]

    def __repr__(self) -> str:
        """Provide human readable debug representation."""
        return f"Instruction(op={self.operation}, mode={self.mode}, operand={self.operand})"


class _ISA_entry(NamedTuple):
    operation: Operation
    mode: AddressMode


class _ISA:
    def __init__(self):
        self.opcode_map = {
            0x00: _ISA_entry(Operation.BRK, AddressMode.Implicit),
            0x18: _ISA_entry(Operation.CLC, AddressMode.Implicit),
            0x38: _ISA_entry(Operation.SEC, AddressMode.Implicit),
            0x48: _ISA_entry(Operation.PHA, AddressMode.Implicit),
            0x4C: _ISA_entry(Operation.JMP, AddressMode.Absolute),
            0x61: _ISA_entry(Operation.ADC, AddressMode.IndirectX),
            0x65: _ISA_entry(Operation.ADC, AddressMode.ZeroPage),
            0x68: _ISA_entry(Operation.PLA, AddressMode.Implicit),
            0x69: _ISA_entry(Operation.ADC, AddressMode.Immediate),
            0x6C: _ISA_entry(Operation.JMP, AddressMode.Indirect),
            0x6D: _ISA_entry(Operation.ADC, AddressMode.Absolute),
            0x71: _ISA_entry(Operation.ADC, AddressMode.IndirectY),
            0x75: _ISA_entry(Operation.ADC, AddressMode.ZeroPageX),
            0x79: _ISA_entry(Operation.ADC, AddressMode.AbsoluteY),
            0x7D: _ISA_entry(Operation.ADC, AddressMode.AbsoluteX),
            0x81: _ISA_entry(Operation.STA, AddressMode.IndirectX),
            0x84: _ISA_entry(Operation.STY, AddressMode.ZeroPage),
            0x85: _ISA_entry(Operation.STA, AddressMode.ZeroPage),
            0x86: _ISA_entry(Operation.STX, AddressMode.ZeroPage),
            0x88: _ISA_entry(Operation.DEY, AddressMode.Implicit),
            0x8D: _ISA_entry(Operation.STA, AddressMode.Absolute),
            0x8C: _ISA_entry(Operation.STY, AddressMode.Absolute),
            0x8E: _ISA_entry(Operation.STX, AddressMode.Absolute),
            0x91: _ISA_entry(Operation.STA, AddressMode.IndirectY),
            0x94: _ISA_entry(Operation.STY, AddressMode.ZeroPageX),
            0x95: _ISA_entry(Operation.STA, AddressMode.ZeroPageX),
            0x96: _ISA_entry(Operation.STX, AddressMode.ZeroPageY),
            0x99: _ISA_entry(Operation.STA, AddressMode.AbsoluteY),
            0x9D: _ISA_entry(Operation.STA, AddressMode.AbsoluteX),
            0xA0: _ISA_entry(Operation.LDY, AddressMode.Immediate),
            0xA1: _ISA_entry(Operation.LDA, AddressMode.IndirectX),
            0xA2: _ISA_entry(Operation.LDX, AddressMode.Immediate),
            0xA4: _ISA_entry(Operation.LDY, AddressMode.ZeroPage),
            0xA5: _ISA_entry(Operation.LDA, AddressMode.ZeroPage),
            0xA6: _ISA_entry(Operation.LDX, AddressMode.ZeroPage),
            0xA9: _ISA_entry(Operation.LDA, AddressMode.Immediate),
            0xAC: _ISA_entry(Operation.LDY, AddressMode.Absolute),
            0xAD: _ISA_entry(Operation.LDA, AddressMode.Absolute),
            0xAE: _ISA_entry(Operation.LDX, AddressMode.Absolute),
            0xB1: _ISA_entry(Operation.LDA, AddressMode.IndirectY),
            0xB4: _ISA_entry(Operation.LDY, AddressMode.ZeroPageX),
            0xB5: _ISA_entry(Operation.LDA, AddressMode.ZeroPageX),
            0xB6: _ISA_entry(Operation.LDX, AddressMode.ZeroPageY),
            0xB9: _ISA_entry(Operation.LDA, AddressMode.AbsoluteY),
            0xBC: _ISA_entry(Operation.LDY, AddressMode.AbsoluteX),
            0xBD: _ISA_entry(Operation.LDA, AddressMode.AbsoluteX),
            0xBE: _ISA_entry(Operation.LDX, AddressMode.AbsoluteY),
            0xC1: _ISA_entry(Operation.CMP, AddressMode.IndirectX),
            0xC5: _ISA_entry(Operation.CMP, AddressMode.ZeroPage),
            0xC6: _ISA_entry(Operation.DEC, AddressMode.ZeroPage),
            0xC8: _ISA_entry(Operation.INY, AddressMode.Implicit),
            0xC9: _ISA_entry(Operation.CMP, AddressMode.Immediate),
            0xCA: _ISA_entry(Operation.DEX, AddressMode.Implicit),
            0xCD: _ISA_entry(Operation.CMP, AddressMode.Absolute),
            0xCE: _ISA_entry(Operation.DEC, AddressMode.Absolute),
            0xD0: _ISA_entry(Operation.BNE, AddressMode.Relative),
            0xD1: _ISA_entry(Operation.CMP, AddressMode.IndirectY),
            0xD5: _ISA_entry(Operation.CMP, AddressMode.ZeroPageX),
            0xD6: _ISA_entry(Operation.DEC, AddressMode.ZeroPageX),
            0xDD: _ISA_entry(Operation.CMP, AddressMode.AbsoluteX),
            0xDE: _ISA_entry(Operation.DEC, AddressMode.AbsoluteX),
            0xD9: _ISA_entry(Operation.CMP, AddressMode.AbsoluteY),
            0xE1: _ISA_entry(Operation.SBC, AddressMode.IndirectX),
            0xE5: _ISA_entry(Operation.SBC, AddressMode.ZeroPage),
            0xE6: _ISA_entry(Operation.INC, AddressMode.ZeroPage),
            0xE8: _ISA_entry(Operation.INX, AddressMode.Implicit),
            0xE9: _ISA_entry(Operation.SBC, AddressMode.Immediate),
            0xEA: _ISA_entry(Operation.NOP, AddressMode.Implicit),
            0xED: _ISA_entry(Operation.SBC, AddressMode.Absolute),
            0xEE: _ISA_entry(Operation.INC, AddressMode.Absolute),
            0xF0: _ISA_entry(Operation.BEQ, AddressMode.Relative),
            0xF1: _ISA_entry(Operation.SBC, AddressMode.IndirectY),
            0xF5: _ISA_entry(Operation.SBC, AddressMode.ZeroPageX),
            0xF6: _ISA_entry(Operation.INC, AddressMode.ZeroPageX),
            0xF9: _ISA_entry(Operation.SBC, AddressMode.AbsoluteY),
            0xFE: _ISA_entry(Operation.INC, AddressMode.AbsoluteX),
            0xFD: _ISA_entry(Operation.SBC, AddressMode.AbsoluteX),
        }

        self.opcode_index: dict[Operation, list[tuple[int, _ISA_entry]]] = {}

        for operation in Operation:
            self.opcode_index[operation] = []

        for opcode, isa_entry in self.opcode_map.items():
            self.opcode_index[isa_entry.operation].append((opcode, isa_entry))

    def __getitem__(self, key: int) -> _ISA_entry:
        return self.opcode_map[key]


_isa = _ISA()
