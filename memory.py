"""
This module defines the memory class used as system memory for our emulated computer.

Classes:
    MemoryMapView - A zero copy view into a MemoryMap object
    MemoryMap - Models the system's memory map
    MemorySegment - A contiguous region of memory
    RamSegment - A ram memory area
    RomSegment - A rom memory area
"""

from abc import ABC, abstractmethod
from bisect import bisect_right
from functools import total_ordering
from pathlib import Path
from typing import Any, BinaryIO, Self, cast, overload

import cachetools

ADDRESS_SPACE_SIZE = 1024 * 64
LAST_ADDRESS = ADDRESS_SPACE_SIZE - 1
CACHE_SIZE = 256


@total_ordering
class MemorySegment(ABC):
    """A contiguous region of memory."""

    def __init__(self, base_address: int, size: int) -> None:
        """Initialize mapping page range."""
        if size > ADDRESS_SPACE_SIZE:
            raise ValueError(f"Allocation is to large, size({size}) > address space size ({ADDRESS_SPACE_SIZE})")
        if (base_address + size) > (ADDRESS_SPACE_SIZE):
            raise ValueError(
                f"Allocation out of bounds, base_address({base_address}) + size({size}) => {base_address + size - 1} which is beyond the last address ({LAST_ADDRESS})"
            )
        self.base_address = base_address
        self.last_address = base_address + size - 1
        self._address_range = range(base_address, base_address + size)

    def _validate_address(self, address: int) -> None:
        if address > LAST_ADDRESS:
            raise ValueError(f"address: 0x{address:04X} is outside of the address space (0x0000-0x{LAST_ADDRESS:04X})")

        if address not in self._address_range:
            raise IndexError

    @abstractmethod
    def __getitem__(self, address: int) -> int:
        """Subscription operator read api."""
        ...

    @abstractmethod
    def __setitem__(self, address: int, value: int) -> None:
        """Subscription operator write api."""
        ...

    def __contains__(self, value: Self | int) -> bool:
        """Containment operator 'a in b' operator api."""
        if not isinstance(value, MemorySegment | int):
            raise TypeError(f"operator not supported for type ({type(value)})")

        if isinstance(value, MemorySegment):
            return self.base_address <= value.base_address and self.last_address >= value.last_address
        else:
            return value in self._address_range

    def __and__(self, value: Self) -> bool:
        """Overloads & (bitwise and) operator, returns true if two MemorySegment objects overlap."""
        if not isinstance(value, MemorySegment):
            return NotImplemented

        return (self.base_address <= value.base_address and value.base_address <= self.last_address) or (
            self.base_address <= value.last_address
            and value.last_address <= self.last_address
            or self.__contains__(value)
            or value.__contains__(self)
        )

    __rand__ = __and__

    def __lt__(self, value: Self) -> bool:
        """Returns true if is this MemorySegment has a lower base address."""
        if not isinstance(value, MemorySegment):
            return NotImplemented

        return self.base_address < value.base_address

    def __eq__(self, value: object) -> bool:
        """
        Returns true is if both MemorySegments have the same base addresses.

        Note that this doesn't take the segments sizes into account.
        """
        if not isinstance(value, MemorySegment):
            return NotImplemented

        return self.base_address == value.base_address


class RamSegment(MemorySegment):
    """A memory segment that is backed by ram."""

    def __init__(self, base_address: int, size: int) -> None:
        """Allocate a bytearray for the segment."""
        super().__init__(base_address, size)

        self._backing_store = bytearray(size)

    def __getitem__(self, address: int) -> int:
        """Retrieve a single byte from ram."""
        self._validate_address(address)

        offset = address - self.base_address
        return self._backing_store[offset]

    def __setitem__(self, address: int, value: int) -> None:
        """Store a single byte to ram."""
        self._validate_address(address)

        if value not in range(0, 256):
            raise ValueError("Only byte values can be stored")

        offset = address - self.base_address
        self._backing_store[offset] = value

    def merge(self, other: Self) -> Self:
        """
        Merge two ram segments.

        Return a new RamSegment object spanning the beginning of the "low" object to
        the end of the "high" object (including any un-allocated address space between them).

        If one RamSegment is fully contained in another this will return a new object with
        the same address space range as the containing object
        """
        new_base_address = min(self.base_address, other.base_address)
        new_last_address = max(self.last_address, other.last_address)
        new_size = new_last_address - new_base_address + 1

        return type(self)(new_base_address, new_size)


class RomSegment(MemorySegment):
    """A memory segment that is backed by rom."""

    def __init__(
        self, base_address: int, *, size: int | None = None, bytes_source: bytes | None = None, binary_file_source: BinaryIO | None = None
    ) -> None:
        """
        Allocate a 'bytes' object for the segment.

        If size is specified, it's allowed to be bigger then size of the source.
        The extra rom will be zero padded. But if it's smaller then the data source,
        A ValueError exception will be raised. Only one of 'bytes_source' or 'binary_file_source'
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

        if size and (size < data_size):
            raise ValueError(f"size ({size}) is too small for data size ({data_size})")

        if size and (size > data_size):
            data = data + bytes(size - data_size)

        if not size:
            size = data_size

        super().__init__(base_address, size)

        self._backing_store = data

    @classmethod
    def from_bytes(cls, base_address: int, bytes_source: bytes) -> Self:
        """Create a RomSegment Class from a bytes object."""
        return cls(base_address, bytes_source=bytes_source)

    @classmethod
    def from_binary_file(cls, base_address: int, path: str | Path) -> Self:
        """Create a RomSegment Class from a file."""
        with open(path, "rb") as f:
            return cls(base_address, binary_file_source=f)

    def __getitem__(self, address: int) -> int:
        """Retrieve a single byte from rom."""
        self._validate_address(address)

        offset = address - self.base_address
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


class MemoryMapView:
    """Zero copy view of a MemoryMap class."""

    def __init__(self, s: slice, mm: "MemoryMap") -> None:
        self.base_address, self.last_address, self.step = s.indices(ADDRESS_SPACE_SIZE)
        self.last_address -= 1

        self.mm = mm

    def __getitem__(self, address) -> int:
        if self.base_address + address * self.step > self.last_address:
            raise IndexError

        return self.mm[self.base_address + address * self.step]

    def __setitem__(self, address, value) -> None:
        if self.base_address + address * self.step > self.last_address:
            raise IndexError

        self.mm[self.base_address + address * self.step] = value

    def __iter__(self):
        i = self.base_address
        while i <= self.last_address:
            yield self.mm[i]
            i += self.step

    def __len__(self) -> int:
        return len(range(self.base_address, self.last_address + 1, self.step))
        # return (self.last_address - self.base_address + 1) // self.step

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, (MemoryMapView, bytes, bytearray)):
            return NotImplemented
        if len(self) != len(other):
            return False

        return all(n == other[i] for i, n in enumerate(self))


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
        self._cache = cachetools.LRUCache(maxsize=CACHE_SIZE)

        ram_list: list[RamSegment] = []
        other_list: list[MemorySegment] = []

        for segment in memory_segments:
            if isinstance(segment, RamSegment):
                ram_list.append(segment)
            elif isinstance(segment, MemorySegment):
                other_list.append(segment)
            else:
                raise ValueError(f"Argument: {segment} type ({type(segment)}) is invalid")

        ram_list = sorted(ram_list)

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

        # This is here to fix a circular dependency issue
        from mmio import Device

        self.hardware_map: list[Device] = []
        for other_segment in other_list:
            for segment in self._memory_map:
                if other_segment & segment:
                    raise RuntimeError(f"Can't allocate segment ({other_segment}), it overlaps with segment ({segment})")

            self._memory_map.append(other_segment)

        self._memory_map = sorted(self._memory_map)
        self.hardware_map = [device for device in self._memory_map if isinstance(device, Device)]

        self._sorted_base_addresses = tuple(segment.base_address for segment in self._memory_map)

    @overload
    def __getitem__(self, address: int) -> int: ...
    @overload
    def __getitem__(self, address: slice) -> MemoryMapView: ...

    def __getitem__(self, address: int | slice) -> int | MemoryMapView:
        """Read data from to our memory, can ba single byte or a bytes like object for slice operations."""
        if type(address) is int:
            if address in self._cache:
                return self._cache[address]

            segment_idx = bisect_right(self._sorted_base_addresses, address) - 1
            if segment_idx >= 0 and address <= self._memory_map[segment_idx].last_address:
                if type(self._memory_map[segment_idx]) is RamSegment:
                    self._cache[address] = self._memory_map[segment_idx][address]
                    return self._memory_map[segment_idx][address]
                else:
                    return self._memory_map[segment_idx][address]

            return self._default_value
        else:
            assert type(address) is slice
            return MemoryMapView(address, self)

    @overload
    def __setitem__(self, address: int, value: int) -> None: ...

    @overload
    def __setitem__(self, address: slice, value: bytes | bytearray | memoryview) -> None: ...

    def __setitem__(self, address: slice | int, value: int | bytes | bytearray | memoryview) -> None:
        """Write data to our memory, can be a single byte or a bytes like object for slice operations."""
        if isinstance(address, int) and isinstance(value, int):
            if value not in range(0, 256):
                raise ValueError("Only byte values can be stored")

            if address in self._cache:
                del self._cache[address]

            for segment in self._memory_map:
                try:
                    segment[address] = value
                    return
                except IndexError:
                    continue
            return  # If we can't find a mapped segment for our address we just silently drop the write, just like on real hardware!
        elif isinstance(address, slice) and isinstance(value, (bytearray, bytes)):
            index_range = range(*address.indices(ADDRESS_SPACE_SIZE))
            if len(index_range) > len(value):
                raise ValueError("Slice can't be longer then source data")
            for i in index_range:
                self.__setitem__(i, value[i - index_range.start])
        else:
            raise ValueError(f"address type ({type(address)}) or value type ({type(value)}) is not valid")

    def __iter__(self):
        """Allow looping over the memory map."""
        address = 0
        limit = ADDRESS_SPACE_SIZE - 1

        while address <= limit:
            yield self.__getitem__(address)
            address += 1

    def poll_hardware(self) -> None:
        """Poll all hardware devices for input from the host."""
        for device in self.hardware_map:
            device.poll_host()

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
