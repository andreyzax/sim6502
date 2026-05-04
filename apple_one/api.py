"""
This module defines the api between the upper and lower layers of the apple 1 hardware emulation stack.

Classes:
    KeyboardBackend - keyboard backend ABC, defines required api for KeyboardBackend objects
    DisplayBackend -  display backend ABC, defines required api for DisplayBackend objects
"""

from abc import ABC, abstractmethod


class KeyboardBackend(ABC):
    """Base class for keyboard implementation backends."""

    @abstractmethod
    def kb_input_ready(self) -> bool:
        """Poll for keyboard input."""
        ...

    @abstractmethod
    def get_char(self) -> str:
        """Get character from the backend."""
        ...


class DisplayBackend(ABC):
    """Base class for display implementation backends."""

    @abstractmethod
    def put_char(self, char: int) -> None:
        """Output character to the backend."""
        ...
