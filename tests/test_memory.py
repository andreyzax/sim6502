import pytest

from memory import MemoryMap, RamSegment, PAGE_NR, PAGE_SIZE, RomSegment


@pytest.fixture(scope="session")
def simple_memory_map() -> MemoryMap:
    return MemoryMap(
        RamSegment(0, 2560),
        RomSegment.from_bytes(0xFF00, b"\xef" * 256),
    )


@pytest.fixture(scope="session")
def disjoint_memory_map() -> MemoryMap:
    return MemoryMap(RamSegment(0, 768), RamSegment(0xFD00, 768))


@pytest.fixture(scope="session")
def overlapping_memory_map() -> MemoryMap:
    return MemoryMap(RamSegment(0, 1280), RamSegment(0x300, 1280))


def test_memory_map_simple_allocation(simple_memory_map: MemoryMap):
    mm = simple_memory_map

    assert len(mm._memory_map) == 2


def test_disjoint_mm_allocation(disjoint_memory_map: MemoryMap):
    mm = disjoint_memory_map

    assert len(mm._memory_map) == 2


def test_overlapping_mm_allocation(overlapping_memory_map: MemoryMap):
    mm = overlapping_memory_map

    assert len(mm._memory_map) == 1
    assert mm._memory_map[0]._address_range.start == 0
    assert mm._memory_map[0]._address_range.stop == 0x800
    assert mm._memory_map[0].base_address == 0x0
    assert mm._memory_map[0].last_address == 0x7FF


def test_ram_segment(simple_memory_map: MemoryMap):
    base = 0
    size = 2560
    mm = simple_memory_map

    assert mm._memory_map[0].base_address == base
    assert mm._memory_map[0].last_address == base + size - 1
    assert mm._memory_map[0]._address_range.start == base
    assert mm._memory_map[0]._address_range.stop == base + size
    assert isinstance(mm._memory_map[0], RamSegment)
    if isinstance(mm._memory_map[0], RamSegment):  # Yes we already asserted this in the previous line but the type checker doesn't care
        mem_seg = mm._memory_map[0]
        assert len(mem_seg._backing_store) == 2560

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


def test_rom_segment(simple_memory_map: MemoryMap):
    base = 0xFF00
    size = 256
    mm = simple_memory_map
    assert mm._memory_map[1].base_address == base
    assert mm._memory_map[1].last_address == base + size - 1
    assert mm._memory_map[1]._address_range.start == base
    assert mm._memory_map[1]._address_range.stop == base + size
    assert isinstance(mm._memory_map[1], RomSegment)
    if isinstance(mm._memory_map[1], RomSegment):
        mem_seg = mm._memory_map[1]
        assert len(mem_seg._backing_store) == size
        assert all((byte == 0xEF for byte in mem_seg))

        with pytest.raises(IndexError):
            mem_seg[0x0]
        with pytest.raises(IndexError):
            mem_seg[0x0] = 0
        with pytest.raises(IndexError):
            mem_seg[0x0A45]
        with pytest.raises(IndexError):
            mem_seg[0x0A45] = 0

        mem_seg[0xFF00] = 0x0
        assert mem_seg[0xFF00] == 0xEF

        rom_seg = RomSegment.from_bytes(0x6400, b"DEADBEEF" * 16)

        for i in range(0x6400, 0x6400 + 128):
            if i % 8 == 0:
                assert rom_seg[i] == ord("D")
            if i % 8 == 1:
                assert rom_seg[i] == ord("E")
            if i % 8 == 2:
                assert rom_seg[i] == ord("A")
            if i % 8 == 3:
                assert rom_seg[i] == ord("D")
            if i % 8 == 4:
                assert rom_seg[i] == ord("B")
            if i % 8 == 5:
                assert rom_seg[i] == ord("E")
            if i % 8 == 6:
                assert rom_seg[i] == ord("E")
            if i % 8 == 7:
                assert rom_seg[i] == ord("F")

        with pytest.raises(IndexError):
            _ = rom_seg[0x6400 + 128]


def test_simple_memory_map_access(simple_memory_map: MemoryMap):
    mm = simple_memory_map

    mm[0] = 0xFF
    assert mm[0] == 0xFF

    mm[0xEC] = 0x42
    assert mm[0xEC] == 0x42

    assert mm[0x0A00] == 0xFF

    mm[0x0000] = 1
    mm[0x0100] = 2
    mm[0x0200] = 3
    mm[0x0300] = 4
    mm[0x0500] = 5
    mm[0x0600] = 6
    mm[0x0700] = 7
    mm[0x0800] = 8
    mm[0x0900] = 9
    if isinstance(mm._memory_map[0], RamSegment):
        assert mm._memory_map[0]._backing_store[0] == 1
        assert mm._memory_map[0]._backing_store[0x100] == 2
        assert mm._memory_map[0]._backing_store[0x200] == 3
        assert mm._memory_map[0]._backing_store[0x300] == 4
        assert mm._memory_map[0]._backing_store[0x500] == 5
        assert mm._memory_map[0]._backing_store[0x600] == 6
        assert mm._memory_map[0]._backing_store[0x700] == 7
        assert mm._memory_map[0]._backing_store[0x800] == 8
        assert mm._memory_map[0]._backing_store[0x900] == 9

    assert mm[0x0CEF] == 0xFF
    mm[0x0CEF] = 0x00
    assert mm[0x0CEF] == 0xFF

    assert mm[0xFD10] == 0xFF
    assert mm[0xFE20] == 0xFF

    mm[0:4] = b"dead"
    assert mm[0:4] == b"dead"

    assert mm[0] == ord("d")
    assert mm[1] == ord("e")
    assert mm[2] == ord("a")
    assert mm[3] == ord("d")

    assert mm[0xFFF0] == 0xEF
    mm[0xFFF0] = 0x0
    assert mm[0xFFF0] == 0xEF
    assert mm[0xFF00:0xFF10] == b"\xef" * 16
    assert mm[0xFF00:0xFFFF] == b"\xef" * 255
    assert mm[0xFF00:0x10000] == b"\xef" * 256
    assert mm[0xFF00:0x10001] == b"\xef" * 256
    assert mm[0xFF00:0x10002] == b"\xef" * 256
    with pytest.raises(ValueError):
        assert mm[0x10000] == 0xEF


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
