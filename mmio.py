"""
This module defines the core api to interface the cpu to io hardware.

Classes:
    Register - Represents a memory address used to read/write or control a hardware device. A base class meant to
    be sub-classed by concrete implementations. Register objects are contained by device classes which route io requests
    to them and provide global device state, and the actual hardware implementation.

    Device - A subclass of MemorySegment that contains a set of emulated hardware register objects. Is mapped to
    contiguous range of addresses in the memory map. A Device object represents a hardware device in the emulated system.
    The class is an abstract class, that is meant to be sub-classed by actual concrete hardware implementation subclasses.
    The device class contains global state for the device, and the implementation logic (or glue logic calling to external modules).
"""

from abc import ABC, abstractmethod

from memory import MemorySegment


class Register(ABC):
    @abstractmethod
    def read(self) -> int: ...

    @abstractmethod
    def write(self, value: int) -> None: ...


class Device(MemorySegment):
    """Abstract base class interface for io devices."""

    def __init__(self, base_address: int, size: int) -> None:
        super().__init__(base_address, size)

        self.registers: dict[int, Register] = {}

    @abstractmethod
    def poll_host(self) -> None:
        """
        For input devices, this polls the host for new input.

        This method returns no value. It updates the device's internal state
        with the new data and optionally raises an interrupt for the CPU to service the input.
        """
        ...
