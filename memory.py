"""
This module defines the memory class used as system memory for our emulated computer.

Classes:
    MemoryMap - Models the system's memory map
    MemorySegment - A contiguous region of memory
    RamSegment - A ram memory area
"""

from abc import ABC, abstractmethod
from typing import overload

PAGE_SIZE = 256
PAGE_NR = 256  # 256 pages * 256 bytes per page = 64 KiB address space


class MemorySegment(ABC):
    """A contiguous region of memory."""

    def __init__(self, base_page: int, npages: int) -> None:
        """Initialize mapping page range."""
        if (base_page + npages) > (PAGE_NR):
            raise ValueError(
                f"Allocation out of bounds, base_page({base_page}) + size({npages}) == {base_page + npages - 1} which is beyond the last page ({PAGE_NR - 1})"
            )
        self.base_page = base_page
        self._page_range = range(base_page, base_page + npages, 1)

    def _validate_address(self, address: int) -> None:
        if address > (PAGE_SIZE * PAGE_NR) - 1:
            raise ValueError(f"address: {address:X} is bigger then {(PAGE_SIZE * PAGE_NR) - 1:X}")

        page = address >> 8

        if page not in self._page_range:
            raise IndexError

    @abstractmethod
    def __getitem__(self, address: int) -> int: ...
    @abstractmethod
    def __setitem__(self, address: int, value: int) -> None: ...


class RamSegment(MemorySegment):
    """A memory segment that is backed by ram."""

    def __init__(self, base_page: int, npages: int) -> None:
        """Allocate a bytearray for the segment."""
        super().__init__(base_page, npages)

        self._backing_store = bytearray(npages * PAGE_SIZE)

    def __getitem__(self, address: int) -> int:
        """Retrieve a single byte from ram."""
        self._validate_address(address)

        offset = address - self.base_page * PAGE_SIZE
        return self._backing_store[offset]

    def __setitem__(self, address: int, value: int) -> None:
        """Store a single byte to ram."""
        self._validate_address(address)

        if value not in range(0, 256):
            raise ValueError("Only byte values can be stored")

        offset = address - self.base_page * PAGE_SIZE
        self._backing_store[offset] = value


class MemoryMap:
    """
    Models the system's memory map.

    The memory layout can be comprised of several discontinuous regions with unmapped gaps in between.
    6502 memory is divided into 256 byte pages (up to 256 of them). We must always allocate memory in page sized and aligned segments.
    Since they are vital to the operation of the cpu, we always map the first two pages.
    """

    def __init__(self, allocation_list: tuple[tuple[int, int], ...], default_value: int = 0xFF) -> None:
        """
        Accept a variable length tuple of base and size tuples.

        Both the base and size are in units of PAGE_SIZE. Overlapping allocation ranges are silently merged.
        """
        self._default_value = default_value if default_value in range(0, 256) else 0xFF

        self.allocation_ranges = tuple(
            range(base, base + size, 1) for base, size in allocation_list
        )  # Ranges are more convenient for us internally

        self._allocation_bitmap = [False for _ in range(0, PAGE_NR)]
        self._allocation_bitmap[:2] = (True, True)  # Always allocate the zero page and the stack page.

        for r in self.allocation_ranges:
            if r.stop > PAGE_NR:
                raise RuntimeError(f"Allocation range {r} outside the bounds of memory")
            for page in r:
                self._allocation_bitmap[page] = True

        self._memory_map: list[MemorySegment] = []
        inside_range = False
        size = 0
        base_page = 0
        for i, bit in enumerate(self._allocation_bitmap):  # Basic state machine here....
            if bit:
                if inside_range:  # Inside allocated range state, just keep counting it's size
                    size += 1
                else:  # Start of allocated range state, toggle to inside_range, record start page and reset size counter
                    inside_range = True
                    base_page = i
                    size = 1
            else:
                # Past the end of range state, toggle inside_range, Create ram segment and append to memory map, reset size counter.
                if inside_range:
                    inside_range = False
                    self._memory_map.append(RamSegment(base_page=base_page, npages=size))
                    size = 0
                # Implicitly, this is the outside of range state, do nothing here

        if inside_range:
            self._memory_map.append(RamSegment(base_page=base_page, npages=size))

    @overload
    def __getitem__(self, address: int) -> int: ...
    @overload
    def __getitem__(self, address: slice) -> bytes: ...

    def __getitem__(self, address: int | slice) -> int | bytes:
        """Read data from to our memory, can ba single byte or a bytes like object for slice operations."""
        if isinstance(address, int):
            for segment in self._memory_map:
                try:
                    return segment[address]
                except IndexError:
                    continue
            return self._default_value
        else:
            index_range = range(*address.indices(PAGE_SIZE * PAGE_NR))
            return bytes(self.__getitem__(i) for i in index_range)  # Yes we recursively call ourself,
            # shouldn't be an issue since this always calls the other branch of the function
            # which is non recursive.

    @overload
    def __setitem__(self, address: int, value: int) -> None: ...

    @overload
    def __setitem__(self, address: slice, value: bytes | bytearray | memoryview) -> None: ...

    def __setitem__(self, address: slice | int, value: int | bytes | bytearray | memoryview) -> None:
        """Write data to our memory, can be a single byte or a bytes like object for slice operations."""
        if isinstance(address, int) and isinstance(value, int):
            if value not in range(0, 256):
                raise ValueError("Only byte values can be stored")

            for segment in self._memory_map:
                try:
                    segment[address] = value
                    return
                except IndexError:
                    continue
            return  # If we can't find a mapped segment for our address we just silently drop the write, just like on real hardware!
        elif isinstance(address, slice) and isinstance(value, (list, tuple, bytearray, bytes)) and all(isinstance(i, int) for i in value):
            index_range = range(*address.indices(PAGE_SIZE * PAGE_NR))
            if len(index_range) > len(value):
                raise ValueError("Slice can't be longer then source data")
            for i in index_range:
                self.__setitem__(i, value[i - index_range.start])
