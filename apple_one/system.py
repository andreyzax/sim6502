"""
This module implements the Apple 1 system emulator.

Classes:
    AppleOne - The system emulator, consumes hardware implementation objects for the apple 1 input and video interfaces
    and exposes a runtime control api.

"""

import itertools
import time

import config
from apple_one.api import DisplayBackend, KeyboardBackend
from apple_one.devices import Keyboard, Video
from cpu import CPU
from memory import MemoryMap, RamSegment, RomSegment
from runtime import Metrics, System


class AppleOne(System):
    """
    The system emulator, consumes hardware implementation objects for the apple 1 input and video interfaces.

    Assembles and wires up the system and owns the system's component objects. Exposes runtime api to control emulator execution.
    """

    def __init__(self, display_backend: DisplayBackend, keyboard_backend: KeyboardBackend):
        """Consumes keyboard and display backend objects and initializes the internal state of the emulator."""
        self.video = Video(backend=display_backend)
        self.keyboard = Keyboard(backend=keyboard_backend)

        roms = (RomSegment.from_binary_file(base_address=rom[0], path=rom[1]) for rom in config.roms)
        self.memory = MemoryMap(RamSegment(0, 0x7FFF), self.video, self.keyboard, *roms)

        reset_addr = self.memory[0xFFFD] << 8 | self.memory[0xFFFC]
        self.cpu = CPU(memory=self.memory, pc=reset_addr)
        self.keyboard.on_reset = self.cpu.reset

        if config.program is not None:
            with open(config.program[1], "rb") as f:
                self.cpu.load(config.program[0], f)

    def step(self, poll_hardware: bool = False) -> None:
        """Execute a single instruction, optionally poll the hardware for pending input."""
        if poll_hardware:
            self.memory.poll_hardware()
        self.cpu.step()

    def run(self) -> Metrics | None:
        """
        Start the cpu's run loop, we only stop due to exceptions.

        Returns a Metrics object or None.
        """
        counter = itertools.count()
        runtime = 0
        try:
            for i in counter:
                if config.enable_runtime_perf_metrics:
                    start = time.perf_counter_ns()

                if i % 10000 == 0:
                    self.step(poll_hardware=True)
                else:
                    self.step()

                if config.enable_runtime_perf_metrics:
                    runtime = runtime + (time.perf_counter_ns() - start)  # pyright: ignore [ reportPossiblyUnboundVariable ]
        except KeyboardInterrupt:
            if config.enable_runtime_perf_metrics:
                instructions = next(counter)
                ips = round(instructions / (runtime / 10**9))
                avg_ins_time = runtime / instructions / 1000  # Show in microseconds

                return Metrics(instructions=instructions, ips=ips, avg_ins_time=avg_ins_time)
            else:
                return None

    def run_for(self, upto: int) -> Metrics | None:
        """
        Run for at most 'upto' instructions.

        Returns a Metrics object or None.
        """
        i = 0
        runtime = 0
        for i in range(0, upto):
            if config.enable_runtime_perf_metrics:
                start = time.perf_counter_ns()

            if i % 10000 == 0:
                self.step(poll_hardware=True)
            else:
                self.step()

            if config.enable_runtime_perf_metrics:
                runtime = runtime + (time.perf_counter_ns() - start)  # pyright: ignore [ reportPossiblyUnboundVariable

        if config.enable_runtime_perf_metrics:
            if i == 0:
                return Metrics(instructions=0, ips=0, avg_ins_time=0)

            i += 1  # turn count into amount
            ips = round(i / (runtime / 10**9))
            avg_ins_time = runtime / i / 1000  # Show in microseconds
            return Metrics(instructions=i, ips=ips, avg_ins_time=avg_ins_time)
        else:
            return None
