import pytest

from contextlib import nullcontext
from typing import Any, NamedTuple
from assembly import Instruction, Operation, AddressMode, EncodingError


def validate_encoding(instruction, encoding):
    assert instruction.machine_code.hex() == encoding.hex(), f"Test instruction: {instruction}"


def validate_encoding_exception(instruction, expectation):
    with expectation:
        instruction.machine_code


def validate_decoding(instruction, encoding):
    assert Instruction.decode(encoding) == instruction


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
def test_implicit_instruction_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_implicit_instruction_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


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
    validate_encoding_exception(input, expectation)


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


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_adc_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


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
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=0x2A), b"\xe9\x2a"),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.ZeroPage, operand=0x2A), b"\xe5\x2a"),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.ZeroPageX, operand=0x2A), b"\xf5\x2a"),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Absolute, operand=0x2A), b"\xed\x2a\x00"),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.AbsoluteX, operand=0x2A), b"\xfd\x2a\x00"),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.AbsoluteY, operand=0x2A), b"\xf9\x2a\x00"),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.IndirectX, operand=0x2A), b"\xe1\x2a"),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.IndirectY, operand=0x2A), b"\xf1\x2a"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_sbc_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_sbc_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.AbsoluteX, operand=0x2A2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.SBC, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_sbc_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x2A), b"\xc9\x2a"),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.ZeroPage, operand=0x2A), b"\xc5\x2a"),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.ZeroPageX, operand=0x2A), b"\xd5\x2a"),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Absolute, operand=0x2A), b"\xcd\x2a\x00"),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.AbsoluteX, operand=0x2A), b"\xdd\x2a\x00"),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.AbsoluteY, operand=0x2A), b"\xd9\x2a\x00"),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.IndirectX, operand=0x2A), b"\xc1\x2a"),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.IndirectY, operand=0x2A), b"\xd1\x2a"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_cmp_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_cmp_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.AbsoluteX, operand=0x2A2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.CMP, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_cmp_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.Relative, operand=0x42), b"\xf0\x42"),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.Relative, operand=0x42), b"\xd0\x42"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_branch_instructions_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_branch_instructions_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.Relative, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.Relative, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.Immediate, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.Absolute, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.AbsoluteX, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.AbsoluteY, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.ZeroPage, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.ZeroPageX, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.ZeroPageY, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.Indirect, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.IndirectX, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.IndirectY, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BEQ, mode=AddressMode.Immediate, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.Absolute, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.AbsoluteX, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.AbsoluteY, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.ZeroPage, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.ZeroPageX, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.ZeroPageY, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.Indirect, operand=0x4242), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.IndirectX, operand=0x42), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.BNE, mode=AddressMode.IndirectY, operand=0x42), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_branch_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.DEC, mode=AddressMode.ZeroPage, operand=0x2A), b"\xc6\x2a"),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.ZeroPageX, operand=0x2A), b"\xd6\x2a"),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.Absolute, operand=0x2A), b"\xce\x2a\x00"),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.AbsoluteX, operand=0x2A), b"\xde\x2a\x00"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_dec_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_dec_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.DEC, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.DEC, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_dec_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.INC, mode=AddressMode.ZeroPage, operand=0x2A), b"\xe6\x2a"),
    Item(Instruction(op=Operation.INC, mode=AddressMode.ZeroPageX, operand=0x2A), b"\xf6\x2a"),
    Item(Instruction(op=Operation.INC, mode=AddressMode.Absolute, operand=0x2A), b"\xee\x2a\x00"),
    Item(Instruction(op=Operation.INC, mode=AddressMode.AbsoluteX, operand=0x2A), b"\xfe\x2a\x00"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_inc_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_inc_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.INC, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INC, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INC, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INC, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INC, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INC, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INC, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INC, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.INC, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_inc_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.JMP, mode=AddressMode.Absolute, operand=0x2A2A), b"\x4c\x2a\x2a"),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.Indirect, operand=0x2A), b"\x6c\x2a\x00"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_jmp_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_jmp_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.JMP, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.ZeroPage, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.ZeroPageX, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.AbsoluteX, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JMP, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_jmp_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.JSR, mode=AddressMode.Absolute, operand=0x2A2A), b"\x20\x2a\x2a"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_jsr_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_jsr_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.JSR, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.ZeroPage, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.ZeroPageX, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.AbsoluteY, operand=0x3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.AbsoluteX, operand=0x3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.JSR, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_jsr_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Immediate, operand=0x2A), b"\xa9\x2a"),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.ZeroPage, operand=0x2A), b"\xa5\x2a"),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.ZeroPageX, operand=0x2A), b"\xb5\x2a"),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Absolute, operand=0x2A), b"\xad\x2a\x00"),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.AbsoluteX, operand=0x2A), b"\xbd\x2a\x00"),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.AbsoluteY, operand=0x2A), b"\xb9\x2a\x00"),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.IndirectX, operand=0x2A), b"\xa1\x2a"),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.IndirectY, operand=0x2A), b"\xb1\x2a"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_lda_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_lda_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.AbsoluteX, operand=0x2A2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDA, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_lda_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Immediate, operand=0x2A), b"\xa2\x2a"),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.ZeroPage, operand=0x2A), b"\xa6\x2a"),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.ZeroPageY, operand=0x2A), b"\xb6\x2a"),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Absolute, operand=0x2A), b"\xae\x2a\x00"),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.AbsoluteY, operand=0x2A), b"\xbe\x2a\x00"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_ldx_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_ldx_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.ZeroPageY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.AbsoluteX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDX, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_ldx_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Immediate, operand=0x2A), b"\xa0\x2a"),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.ZeroPage, operand=0x2A), b"\xa4\x2a"),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.ZeroPageX, operand=0x2A), b"\xb4\x2a"),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Absolute, operand=0x2A), b"\xac\x2a\x00"),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.AbsoluteX, operand=0x2A), b"\xbc\x2a\x00"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_ldy_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_ldy_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.ZeroPageY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.AbsoluteX, operand=0x2A2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.LDY, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_ldy_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.STA, mode=AddressMode.ZeroPage, operand=0x2A), b"\x85\x2a"),
    Item(Instruction(op=Operation.STA, mode=AddressMode.ZeroPageX, operand=0x2A), b"\x95\x2a"),
    Item(Instruction(op=Operation.STA, mode=AddressMode.Absolute, operand=0x2A), b"\x8d\x2a\x00"),
    Item(Instruction(op=Operation.STA, mode=AddressMode.AbsoluteX, operand=0x2A), b"\x9d\x2a\x00"),
    Item(Instruction(op=Operation.STA, mode=AddressMode.AbsoluteY, operand=0x2A), b"\x99\x2a\x00"),
    Item(Instruction(op=Operation.STA, mode=AddressMode.IndirectX, operand=0x2A), b"\x81\x2a"),
    Item(Instruction(op=Operation.STA, mode=AddressMode.IndirectY, operand=0x2A), b"\x91\x2a"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_sta_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_sta_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.STA, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.AbsoluteX, operand=0x2A2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STA, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_sta_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.STX, mode=AddressMode.ZeroPage, operand=0x2A), b"\x86\x2a"),
    Item(Instruction(op=Operation.STX, mode=AddressMode.ZeroPageY, operand=0x2A), b"\x96\x2a"),
    Item(Instruction(op=Operation.STX, mode=AddressMode.Absolute, operand=0x2A), b"\x8e\x2a\x00"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_stx_encoding(input, expected):
    validate_encoding(input, expected)


test_matrix = [
    Item(Instruction(op=Operation.STX, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.ZeroPageY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.AbsoluteX, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STX, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_stx_instructions(input, expectation):
    validate_encoding_exception(input, expectation)


test_matrix = [
    Item(Instruction(op=Operation.STY, mode=AddressMode.ZeroPage, operand=0x2A), b"\x84\x2a"),
    Item(Instruction(op=Operation.STY, mode=AddressMode.ZeroPageX, operand=0x2A), b"\x94\x2a"),
    Item(Instruction(op=Operation.STY, mode=AddressMode.Absolute, operand=0x2A), b"\x8c\x2a\x00"),
]


@pytest.mark.parametrize(
    "input,expected",
    test_matrix,
    ids=[f"{item.instruction.operation.name}_{item.instruction.mode.name}" for item in test_matrix],
)
def test_sty_encoding(input, expected):
    validate_encoding(input, expected)


@pytest.mark.parametrize(
    "instruction,encoding",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_sty_decoding(instruction, encoding):
    validate_decoding(instruction, encoding)


test_matrix = [
    Item(Instruction(op=Operation.STY, mode=AddressMode.Implicit, operand=None), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.Implicit, operand=0x0), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.Implicit, operand=0xFEFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.Immediate, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.ZeroPage, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.ZeroPageX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.ZeroPageY, operand=0x2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.Absolute, operand=0xFFFFF), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.AbsoluteX, operand=0x2A2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.AbsoluteY, operand=0x3C3C3C), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.Indirect, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.IndirectX, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.IndirectY, operand=0x2A2A), pytest.raises(EncodingError)),
    Item(Instruction(op=Operation.STY, mode=AddressMode.Relative, operand=0x2A), pytest.raises(EncodingError)),
]


@pytest.mark.parametrize(
    "input,expectation",
    test_matrix,
    ids=[item.instruction.operation.name for item in test_matrix],
)
def test_invalid_sty_instructions(input, expectation):
    validate_encoding_exception(input, expectation)
