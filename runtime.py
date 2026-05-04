"""
This module defines runtime control and dependency injection machinery classes.

Classes:
    Metrics - Runtime metrics statistics data
    System - Base class for system controller classes
    Runtime - Base class for runtime controller classes

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self

from cpu import CPU
from memory import MemoryMap


@dataclass
class Metrics:
    """
    Aggregated metrics data from a cpu execution run.

    instructions - number of instructions executed.
    ips - instructions per second.
    avg_ins_time - average instruction execution time.
    """

    instructions: int
    ips: int
    avg_ins_time: float  # microseconds

    def __add__(self, other: Self | None) -> Self:
        """
        Add two Metrics objects.

        Return a new Metrics object with aggregated statistics counters.
        Has special handling for
        """
        # Special case for things like:
        # accumulator = None
        # ...
        # accumulator = accumulator + Metrics(...)
        if other is None:
            return type(self)(instructions=self.instructions, ips=self.ips, avg_ins_time=self.avg_ins_time)

        if not isinstance(other, type(self)):
            return NotImplemented

        total_instructions = self.instructions + other.instructions
        new_ips = (self.ips * self.instructions + other.ips * other.instructions) / total_instructions
        new_avg_ins_time = (self.avg_ins_time * self.instructions + other.avg_ins_time * other.instructions) / total_instructions
        return type(self)(
            instructions=total_instructions,
            ips=round(new_ips),
            avg_ins_time=new_avg_ins_time,
        )

    __radd__ = __add__  # Make self + other equvilent to other + self

    def __iadd__(self, other: Self | None) -> Self:
        """Self increment version of __add__()."""
        if not isinstance(other, type(self)):
            return NotImplemented

        total_instructions = self.instructions + other.instructions
        new_ips = (self.ips * self.instructions + other.ips * other.instructions) / total_instructions
        new_avg_ins_time = (self.avg_ins_time * self.instructions + other.avg_ins_time * other.instructions) / total_instructions

        self.instructions = total_instructions
        self.ips = round(new_ips)
        self.avg_ins_time = new_avg_ins_time

        return self

    def __str__(self) -> str:
        """Human readable representation."""
        return f"Instructions: {self.instructions}, ips: {self.ips:,}, average instruction time: {self.avg_ins_time:.3f}us"


class System(ABC):
    """
    Base class for system controller classes.

    This class assembles and owns the emulated systems component classes.
    It exposes a runtime control api for the Runtime class.
    """

    @abstractmethod
    def step(self, poll_hardware: bool = False) -> None:
        """Execute one instruction and optionally poll the hardware."""
        ...

    @abstractmethod
    def run_for(self, upto: int) -> Metrics | None:
        """Run for at most 'upto' instructions."""
        ...

    @property
    @abstractmethod
    def cpu(self) -> CPU:
        """Get the systems cpu."""
        ...

    @property
    @abstractmethod
    def memory(self) -> MemoryMap:
        """Get the systems memory."""
        ...


class Runtime(ABC):
    """
    Base class for runtime controller classes.

    The api is the similar to the the System class, but they
    have a different function. This class is a thin wrapper over a system object
    and an interface between the system object and ui.
    """

    @abstractmethod
    def step(self, poll_hardware: bool = False) -> None:
        """Execute one instruction and optionally poll the hardware."""
        ...

    @abstractmethod
    def run_for(self, upto: int) -> Metrics | None:
        """Run for at most 'upto' instructions."""
        ...

    @abstractmethod
    def run(self) -> None:
        """Start the runtime."""
        ...

    @property
    @abstractmethod
    def cpu(self) -> CPU:
        """Get the runtime CPU state."""
        ...

    @property
    @abstractmethod
    def memory(self) -> MemoryMap:
        """Get the runtime memory."""
        ...
