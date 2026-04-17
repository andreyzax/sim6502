import pytest

from memory import MemoryMap, RamSegment, PAGE_NR, PAGE_SIZE


@pytest.fixture(scope="session")
def simple_memory_map() -> MemoryMap:
    return MemoryMap(((0, 10),))


@pytest.fixture(scope="session")
def disjoint_memory_map() -> MemoryMap:
    return MemoryMap(((0, 3), (253, 3)))


@pytest.fixture(scope="session")
def overlapping_memory_map() -> MemoryMap:
    return MemoryMap(((0, 5), (3, 5)))


def test_memory_map_simple_allocation(simple_memory_map: MemoryMap):
    size = 10
    mm = simple_memory_map

    assert len(mm._allocation_bitmap) == PAGE_NR
    assert all(mm._allocation_bitmap[0 : size - 1])
    assert not any(mm._allocation_bitmap[size:])
    assert len(mm._memory_map) == 1


def test_disjoint_mm_allocation(disjoint_memory_map: MemoryMap):
    mm = disjoint_memory_map

    assert all(mm._allocation_bitmap[:3])
    assert all(mm._allocation_bitmap[253:])
    assert not any(mm._allocation_bitmap[3:253])
    assert len(mm._memory_map) == 2


def test_overlapping_mm_allocation(overlapping_memory_map: MemoryMap):
    mm = overlapping_memory_map

    assert all(mm._allocation_bitmap[:8])
    assert not any(mm._allocation_bitmap[8:])

    assert len(mm._memory_map) == 1
    assert mm._memory_map[0]._page_range.start == 0
    assert mm._memory_map[0]._page_range.stop == 8


def test_ram_segment(simple_memory_map: MemoryMap):
    base = 0
    size = 10
    mm = simple_memory_map

    assert mm._memory_map[0].base_page == base
    assert mm._memory_map[0]._page_range.start == base
    assert mm._memory_map[0]._page_range.stop == base + size
    assert isinstance(mm._memory_map[0], RamSegment)
    if isinstance(mm._memory_map[0], RamSegment):  # Yes we already asserted this in the previous line but the type checker doesn't care
        mem_seg = mm._memory_map[0]
        assert len(mem_seg._backing_store) == 10 * PAGE_SIZE

        with pytest.raises(IndexError):
            mem_seg[0xA00]
        with pytest.raises(IndexError):
            mem_seg[-1]

        assert mem_seg[0] == 0
        mem_seg[0] = 0xA1
        assert mem_seg[0] == 0xA1
        mem_seg[0xFF] = 0xA1
        assert mem_seg[0xFF] == 0xA1
        mem_seg[0xFF] = 0x42
        assert mem_seg[0xFF] == 0x42


def test_simple_memory_map_access(simple_memory_map):
    mm = simple_memory_map

    mm[0] = 0xFF
    assert mm[0] == 0xFF

    mm[0xEC] = 0x42
    assert mm[0xEC] == 0x42

    assert mm[0x0A00] == 0xFF

    assert mm[0x0CEF] == 0xFF
    mm[0x0CEF] = 0x00
    assert mm[0x0CEF] == 0xFF

    assert mm[0xFD10] == 0xFF
    assert mm[0xFE20] == 0xFF
    assert mm[0xFFF0] == 0xFF

    mm[0:4] = b"dead"
    assert mm[0:4] == b"dead"

    assert mm[0] == ord("d")
    assert mm[1] == ord("e")
    assert mm[2] == ord("a")
    assert mm[3] == ord("d")


def test_disjoint_memory_map_access(disjoint_memory_map):
    mm = disjoint_memory_map

    mm[0] = 0x12
    assert mm[0] == 0x12

    mm[0xEC] = 0x42
    assert mm[0xEC] == 0x42

    assert mm[0x0A00] == mm._default_value
    mm[0x0A00] = 0x5C
    assert mm[0x0CEF] == mm._default_value

    mm[0x0CEF] = 0x00
    assert mm[0x0CEF] == mm._default_value

    assert mm[0xFD10] == 0x00
    assert mm[0xFE20] == 0x00
    assert mm[0xFFF0] == 0x00

    mm[0:4] = b"dead"
    assert mm[:4] == b"dead"
    assert mm[0] == ord("d")
    assert mm[1] == ord("e")
    assert mm[2] == ord("a")
    assert mm[3] == ord("d")
    mm[0x8000:4] = b"dead"
    assert mm[0x8000:0x8004] == b"\xff\xff\xff\xff"

    assert mm[0x8000] == 0xFF
    assert mm[0x8001] == 0xFF
    assert mm[0x8002] == 0xFF
    assert mm[0x8003] == 0xFF

    mm[0xFE00:0xFE04] = b"dead"
    assert mm[0xFE00:0xFE04] == b"dead"
    mm[0xFE00:0xFE02] = b"to"
    assert mm[0xFE00:0xFE04] == b"toad"
    mm[0xFE00] = ord("r")
    assert mm[0xFE00:0xFE04] == b"road"
    mm[0xFE00:0xFE03] = b"bro"
    assert mm[0xFE00:0xFE04] == b"brod"
    mm[0xFE00:0xFE02] = b"form"
    assert mm[0xFE00:0xFE04] == b"food"  # Only the first two bytes are copied since the slice is only two bytes wide
    # We don't support python's standard slice insert semantics (can hardly add memory capacity!)
    # we simply ignore the rest of the data that won't fit into our slice

    with pytest.raises(ValueError):
        mm[0xFE00:0xFE05] = b"form"  # We don't support python's standard delete and replace semantics.
        # (what would that even look like for a fixed sized memory array)
        # If the slice is larger then the source data we raise an exception
