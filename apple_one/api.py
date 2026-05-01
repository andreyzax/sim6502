"""This module defines the api between the upper and lower layers of the apple 1 hardware emulation stack."""

from abc import ABC, abstractmethod


class KeyboardBackend(ABC):
    @abstractmethod
    def kb_input_ready(self) -> bool: ...

    @abstractmethod
    def get_char(self) -> str: ...


class DisplayBackend(ABC):
    @abstractmethod
    def put_char(self, char: int) -> None: ...
