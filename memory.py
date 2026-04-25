"""
This module defines the memory class used as system memory for our emulated computer.

Classes:
    MemoryMap - Models the system's memory map
    MemorySegment - A contiguous region of memory
    RamSegment - A ram memory area
    RomSegment - A rom memory area
"""

from abc import ABC, abstractmethod
from functools import total_ordering
from pathlib import Path
from typing import BinaryIO, Self, cast, overload

PAGE_SIZE = 256
PAGE_NR = 256  # 256 pages * 256 bytes per page = 64 KiB address space
ADDRESS_SPACE_SIZE = 1024 * 64


@total_ordering
class MemorySegment(ABC):
    """A contiguous region of memory."""

    def __init__(self, base_page: int, npages: int) -> None:
        """Initialize mapping page range."""
        if npages * PAGE_SIZE > ADDRESS_SPACE_SIZE:
            raise ValueError(f"Allocation is to large, npages({npages}) * page size{PAGE_SIZE} > address space size ({ADDRESS_SPACE_SIZE})")
        if (base_page + npages) > (PAGE_NR):
            raise ValueError(
                f"Allocation out of bounds, base_page({base_page}) + size({npages}) == {base_page + npages - 1} which is beyond the last page ({PAGE_NR - 1})"
            )
        self.base_page = base_page
        self.last_page = base_page + npages - 1
        self._page_range = range(base_page, base_page + npages, 1)

    def _validate_address(self, address: int) -> None:
        if address > (PAGE_SIZE * PAGE_NR) - 1:
            raise ValueError(f"address: {address:X} is bigger then {(PAGE_SIZE * PAGE_NR) - 1:X}")

        page = address >> 8

        if page not in self._page_range:
            raise IndexError

    @abstractmethod
    def __getitem__(self, address: int) -> int:
        """Subscription operator read api."""
        ...

    @abstractmethod
    def __setitem__(self, address: int, value: int) -> None:
        """Subscription operator write api."""
        ...

    def __contains__(self, value: Self) -> bool:
        """Containment operator 'a in b' operator api."""
        if not isinstance(value, MemorySegment):
            return NotImplemented

        return self.base_page <= value.base_page and self.last_page >= value.last_page

    def __and__(self, value: Self) -> bool:
        if not isinstance(value, MemorySegment):
            return NotImplemented

        return (self.base_page <= value.base_page and value.base_page <= self.last_page) or (
            self.base_page <= value.last_page and value.last_page <= self.last_page
        )

    __rand__ = __and__

    def __lt__(self, value: Self) -> bool:
        if not isinstance(value, MemorySegment):
            return NotImplemented

        return self.base_page < value.base_page

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, MemorySegment):
            return NotImplemented

        return self.base_page == value.base_page


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

    def merge(self, other: Self) -> Self:
        """
        Merge two ram segments.

        Return a new RamSegment object spanning the beginning of the "low" object to
        the end of the "high" object (including any un-allocated address space between them).

        If one RamSegment is fully contained in another this will return a new object with
        the same address space range as the containing object
        """
        new_base_page = min(self.base_page, other.base_page)
        new_last_page = max(self.last_page, other.last_page)
        new_npages = new_last_page - new_base_page + 1

        return type(self)(new_base_page, new_npages)


class RomSegment(MemorySegment):
    """A memory segment that is backed by rom."""

    def __init__(
        self, base_page: int, *, npages: int | None = None, bytes_source: bytes | None = None, binary_file_source: BinaryIO | None = None
    ) -> None:
        """
        Allocate a 'bytes' object for the segment.

        If napages is specified, it's allowed to be bigger then size of the source.
        The extra rom will be zero padded. But if it's smaller then the data source,
        A ValueError excpetion will be raised. Only one of 'bytes_source' or 'binary_file_source'
        must be specified.
        """
        if bool(bytes_source) == bool(binary_file_source):
            raise ValueError("You must pass in *one* and *only one* of 'bytes_source' or 'binary_file_source'")

        if bytes_source:
            data_size = len(bytes_source)
            data = bytes_source
        else:
            binary_file_source = cast(BinaryIO, binary_file_source)
            data = binary_file_source.read(ADDRESS_SPACE_SIZE)

            if binary_file_source.read(1):
                raise RuntimeError("File source is to big to fit in memory")

            data_size = len(data)

        if npages and (npages * PAGE_SIZE < data_size):
            raise ValueError(f"npages ({npages}) is too small for data size ({data_size})")

        if not npages:
            npages = data_size // PAGE_SIZE
            npages = npages + (0 if npages * PAGE_SIZE == data_size else 1)

        super().__init__(base_page, npages)

        self._backing_store = data + (b"\x00" * ((npages * PAGE_SIZE) - data_size))

    @classmethod
    def from_bytes(cls, base_page: int, bytes_source: bytes) -> Self:
        """Create a RomSegment Class from a bytes object."""
        return cls(base_page, bytes_source=bytes_source)

    @classmethod
    def from_binary_file(cls, base_page: int, path: str | Path) -> Self:
        """Create a RomSegment Class from a file."""
        with open(path, "rb") as f:
            return cls(base_page, binary_file_source=f)

    def __getitem__(self, address: int) -> int:
        """Retrieve a single byte from rom."""
        self._validate_address(address)

        offset = address - self.base_page * PAGE_SIZE
        return self._backing_store[offset]

    def __setitem__(self, address: int, value: int) -> None:
        """
        Handle write requests to rom.

        While it's obviously impossible to write to rom we still need to have a callable
        __setitem__ method to:
            1. satisfy the base class api
            2. "handle" writes, while the 6502 didn't have any memory protection or "invalid" access trap
               mechanism for us to emulate and writes to rom would be silently thrown away, we still need
               a __setitem__ method to accept the writes (and throw them away like the hardware would)
            3. finally, for our internal api we need the RomSegment to raise IndexError exceptions when the write
               is outside the segment's page bounds, that is a normal code path that the memory map class uses
               in it's address resolution algorithm. We will get write attempts that aren't meant for us and need
               to respond with IndexError as part of the MemoryMap <-> MemorySegment api
        """
        self._validate_address(address)  # Here to raise IndexError exceptions, we do nothing with the actual value!


class MemoryMap:
    """
    Models the system's memory map.

    The memory layout can be comprised of several discontinuous regions with unmapped gaps in between.
    6502 memory is divided into 256 byte pages (up to 256 of them). We must always allocate memory in page sized and aligned segments.
    Since they are vital to the operation of the cpu, we always map the first two pages.
    """

    def __init__(self, *memory_segments: MemorySegment, default_value: int = 0xFF) -> None:
        """
        Accept a list of ram and rom segment objects.

        Merge overlapping ram and rom segments separately but disallow ram overlapping with rom
        """
        self._default_value = default_value if default_value in range(0, 256) else 0xFF

        ram_list: list[RamSegment] = []
        rom_list: list[RomSegment] = []

        for segment in memory_segments:
            if isinstance(segment, RamSegment):
                ram_list.append(segment)
            elif isinstance(segment, RomSegment):
                rom_list.append(segment)
            else:
                raise ValueError(f"Argument: {segment} type ({type(segment)}) is invalid")

        ram_list = sorted(ram_list)
        # rom_list = sorted(rom_list)

        # It's important for this code that the list be sorted, it depends on the line above
        i = 0
        length = len(ram_list)
        merged_ram_list: list[RamSegment] = []
        if length > 1:
            while i < length - 1:  # we iterate to the second to last element since we can't merge the last element with anything.
                if ram_list[i] & ram_list[i + 1]:
                    merged_ram_list.append(ram_list[i].merge(ram_list[i + 1]))
                    i += 2
                else:
                    merged_ram_list.append(ram_list[i])
                    i += 1
            if i < length:  # Take care of the last element if it's not merged
                merged_ram_list.append(ram_list[i])
        else:
            merged_ram_list = ram_list

        self._memory_map: list[MemorySegment] = list(merged_ram_list)

        for rom_segment in rom_list:
            for segment in self._memory_map:
                if rom_segment & segment:
                    raise RuntimeError(f"Can't allocate RomSegment ({rom_segment}), it overlaps with segment ({segment})")

            self._memory_map.append(rom_segment)

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

    def __iter__(self):
        """Allow looping over the memory map."""
        address = 0
        limit = ADDRESS_SPACE_SIZE - 1

        while address <= limit:
            yield self.__getitem__(address)
            address += 1

    def dump(self) -> str:
        """Dump the contents of the memory map."""
        content: list[str] = []
        for address, value in enumerate(self):
            if address % 16 == 0:
                content.append(f"\n{address:04X}: {value:02X}")
            elif address % 2 == 0:
                content.append(" ")

            content.append(f" {value:02X}")

        return "".join(content)
