"""
This module defines runtime control and dependency injection machinery classes.

Classes:
    Metrics - Runtime metrics statistics data
    System - Base class for runtime controller classes

"""

from abc import ABC, abstractmethod
from typing import NamedTuple


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
    """Base class for runtime controller classes."""

    @abstractmethod
    def step(self, poll_hardware: bool = False) -> None:
        """Execute one instruction and optionally poll the hardware."""
        ...

    @abstractmethod
    def run_for(self, upto: int) -> Metrics | None:
        """Run for at most 'upto' instructions."""
        ...
