import pytest

from contextlib import nullcontext
from typing import Any, NamedTuple
from assembly import Instruction, Operation, AddressMode, EncodingError


def validate_encoding(instruction, encoding):
    assert instruction.machine_code.hex() == encoding.hex(), f"Test instruction: {instruction}"


def validate_encoding_exception(instruction, expectation):
    with expectation:
        instruction.machine_code


class Item(NamedTuple):
    instruction: Instruction
    expected: Any


test_matrix = [
    Item(Instruction(op=Operation.BRK, mode=AddressMode.Implicit, operand=None), b"\x00"),
    Item(Instruction(op=Operation.CLC, mode=AddressMode.Implicit, operand=None), b"\x18"),
    Item(Instruction(op=Operation.SEC, mode=AddressMode.Implicit, operand=None), b"\x38"),
    Item(Instruction(op=Operation.PHA, mode=AddressMode.Implicit, operand=None), b"\x48"),
    Item(Instruction(op=Operation.PLA, mode=AddressMode.Implicit, operand=None), b"\x68"),
    Item(Instruction(op=Operation.DEY, mode=AddressMode.Implicit, operand=None), b"\x88"),
    Item(Instruction(op=Operation.INY, mode=AddressMode.Implicit, operand=None), b"\xc8"),
    Item(Instruction(op=Operation.DEX, mode=AddressMode.Implicit, operand=None), b"\xca"),
    Item(Instruction(op=Operation.INX, mode=AddressMode.Implicit, operand=None), b"\xe8"),
    Item(Instruction(op=Operation.NOP, mode=AddressMode.Implicit, operand=None), b"\xea"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_implicit_instruction_decoding(input, expected):
    validate_encoding(input, expected)


test_matrix = [
    Item(Instruction(op=Operation.BRK, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CLC, mode=AddressMode.Implicit, operand=0x1), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SEC, mode=AddressMode.Implicit, operand=0x2), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.PHA, mode=AddressMode.Implicit, operand=0x10), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.PLA, mode=AddressMode.Implicit, operand=0xFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEY, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INY, mode=AddressMode.Implicit, operand=256), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEX, mode=AddressMode.Implicit, operand=1000000), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INX, mode=AddressMode.Implicit, operand=2**32), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.NOP, mode=AddressMode.Implicit, operand=0xFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BRK, mode=AddressMode.Absolute, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CLC, mode=AddressMode.AbsoluteX, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SEC, mode=AddressMode.AbsoluteY, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.PHA, mode=AddressMode.Immediate, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.PLA, mode=AddressMode.Implicit, operand=None), nullcontext()),
    Item(Instruction(op=Operation.DEY, mode=AddressMode.Indirect, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INY, mode=AddressMode.IndirectX, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEX, mode=AddressMode.IndirectY, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INX, mode=AddressMode.Relative, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.NOP, mode=AddressMode.ZeroPage, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BRK, mode=AddressMode.ZeroPageX, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BRK, mode=AddressMode.ZeroPageY, operand=None), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_implicit_instructions(input, expectation):
    with expectation:
        input.machine_code


test_matrix = [
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=0x2A), b"\x69\x2a"),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.ZeroPage, operand=0x2A), b"\x65\x2a"),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.ZeroPageX, operand=0x2A), b"\x75\x2a"),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Absolute, operand=0x2A), b"\x6d\x2a\x00"),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.AbsoluteX, operand=0x2A), b"\x7d\x2a\x00"),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.AbsoluteY, operand=0x2A), b"\x79\x2a\x00"),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.IndirectX, operand=0x2A), b"\x61\x2a"),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.IndirectY, operand=0x2A), b"\x71\x2a"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_adc_encoding(input, expected):
    validate_encoding(input, expected)


test_matrix = [
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.AbsoluteX, operand=0x2A2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.ADC, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_adc_instructions(input, expectation):
    with expectation:
        input.machine_code
