from assembly import Instruction, Operation, AddressMode


def test_instruction_decoding():

    brk = Instruction(op=Operation.BRK, mode=AddressMode.Implicit, operand=None).machine_code
    nop = Instruction(op=Operation.NOP, mode=AddressMode.Implicit, operand=None).machine_code
    assert brk == b"\x00"
    assert nop == b"\xea"
