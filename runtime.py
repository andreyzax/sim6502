"""
This module defines runtime control and dependency injection machinery classes.

Classes:
    Metrics - Runtime metrics statistics data
    System - Base class for system controller classes
    Runtime - Base class for runtime controller classes

"""

from abc import ABC, abstractmethod
from typing import NamedTuple

from cpu import CPU
from memory import MemoryMap


class Metrics(NamedTuple):
    """
    Aggregated metrics data from a cpu execution run.

    instructions - number of instructions executed.
    ips - instructions per second.
    avg_ins_time - average instruction execution time.
    """

    instructions: int
    ips: int
    avg_ins_time: float


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
