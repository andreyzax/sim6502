"""
This module implements the Apple 1 system emulator.

Classes:
    AppleOne - The system emulator, consumes hardware implementation objects for the apple 1 input and video interfaces
    and exposes a runtime control api.
    TerminalRuntime - raw tty based runtime controller, implements the tty emulator.
    TuiRuntime - TUI based runtime controller, implements the tui (textual) emulator.

"""

import itertools
import time

from dynaconf import Dynaconf

import apple_one.terminal as terminal
import apple_one.tui as tui
from apple_one.api import DisplayBackend, KeyboardBackend
from apple_one.devices import Keyboard, Video
from cpu import CPU, CPUTrap
from memory import MemoryMap, RamSegment, RomSegment
from runtime import Metrics, Runtime, System


class AppleOne(System):
    """
    The system emulator, consumes hardware implementation objects for the apple 1 input and video interfaces.

    Assembles and wires up the system and owns the system's component objects. Exposes runtime api to control emulator execution.
    """

    def __init__(self, display_backend: DisplayBackend, keyboard_backend: KeyboardBackend, config: Dynaconf):
        """Consumes keyboard and display backend objects and initializes the internal state of the emulator."""
        self.video = Video(backend=display_backend)
        self.keyboard = Keyboard(backend=keyboard_backend)

        roms = (RomSegment.from_binary_file(base_address=rom.load_address, path=rom.path) for rom in config.get("roms", []))
        self._memory = MemoryMap(RamSegment(0, 0x7FFF), self.video, self.keyboard, *roms)

        reset_addr = self._memory[0xFFFD] << 8 | self._memory[0xFFFC]
        self._cpu = CPU(memory=self._memory, pc=reset_addr, trap_brk=config.get("trap_brk", False))
        self.keyboard.on_reset = self._cpu.reset

        self.collect_metrics: bool = config.get("metrics", False)

        if config.get("program", None) is not None:
            with open(config.program.path, "rb") as f:
                self.cpu.load(config.program.load_address, f)

    def step(self, tick_hardware: bool = False) -> int:
        """Execute a single instruction, optionally advance the hardware state."""
        cycles = self._cpu.step()
        if tick_hardware:
            for device in self.memory.hardware_map:
                device.tick(cycles)
        return cycles

    def run(self) -> Metrics | None:
        """
        Start the cpu's run loop, we only stop due to exceptions.

        Returns a Metrics object or None.
        """
        counter = itertools.count()
        runtime = 0
        run_cycles = 0
        tick_cycles = 0
        ins_cycles = 0
        try:
            for i in counter:
                if self.collect_metrics:
                    start = time.perf_counter_ns()

                if i % 10000 == 0:
                    ins_cycles = self.step(tick_hardware=True)
                    tick_cycles = 0
                else:
                    ins_cycles = self.step()

                tick_cycles += ins_cycles

                if self.collect_metrics:
                    runtime = runtime + (time.perf_counter_ns() - start)  # pyright: ignore [ reportPossiblyUnboundVariable ]
                    run_cycles += ins_cycles

        except KeyboardInterrupt:
            if self.collect_metrics:
                instructions = next(counter)
                ips = round(instructions / (runtime / 10**9))
                avg_ins_time = runtime / instructions / 1000  # Show in microseconds

                return Metrics(runtime=runtime, instructions=instructions, ips=ips, cycles=run_cycles, avg_ins_time=avg_ins_time)
            else:
                return None

    def run_for(self, upto: int) -> Metrics | None:
        """
        Run for at most 'upto' instructions.

        Returns a Metrics object or None.
        """
        i = 0
        runtime = 0
        run_cycles = 0
        tick_cycles = 0
        ins_cycles = 0
        for i in range(0, upto):
            if self.collect_metrics:
                start = time.perf_counter_ns()

            if i % 10000 == 0:
                ins_cycles = self.step(tick_hardware=True)
                tick_cycles = 0
            else:
                ins_cycles = self.step()
            tick_cycles += ins_cycles

            if self.collect_metrics:
                runtime = runtime + (time.perf_counter_ns() - start)  # pyright: ignore [ reportPossiblyUnboundVariable
                run_cycles += ins_cycles

        if self.collect_metrics:
            if i == 0:
                return Metrics(runtime=0, instructions=0, ips=0, cycles=0, avg_ins_time=0)

            i += 1  # turn count into amount
            ips = round(i / (runtime / 10**9))
            avg_ins_time = runtime / i / 1000  # Show in microseconds
            return Metrics(runtime=runtime, instructions=i, ips=ips, cycles=run_cycles, avg_ins_time=avg_ins_time)
        else:
            return None

    @property
    def memory(self) -> MemoryMap:
        """Get the system's memory."""
        return self._memory

    @property
    def cpu(self) -> CPU:
        """Get the system's cpu."""
        return self._cpu


class TerminalRuntime(Runtime):
    """Terminal backed runtime class."""

    def __init__(self, config: Dynaconf):
        """Create a terminal backed runtime."""
        if config.get("tty", None):
            device = open(config.tty, "r+b", buffering=0)  # noqa: SIM115
            terminal.init_backend(device)
        else:
            terminal.init_backend()

        self.system = AppleOne(display_backend=terminal.TerminalDisplayBackend(), keyboard_backend=terminal.TerminalKeyboardBackend(), config=config)

    def _trap_handler(self, cpu: CPU) -> None:
        """Handle cpu traps, currently only gets triggered if `settings.trap_brk` is true."""
        # flags = ("#" if flag else " " for flag in (cpu.p.negative, cpu.p.overflow, True, True, cpu.p.decimal, cpu.p.interrupt_disable, cpu.p.zero, cpu.p.carry))
        # flags_str = "".join(flags)
        print(f"""\nExecution stopped:
            pc=0x{cpu.pc:X}
            ins={cpu._decode()}
            s=0x{cpu.s:X}
            a=0x{cpu.a:X},x=0x{cpu.x:X},y=0x{cpu.y:X}
            flags:   NV-BDIZC
                     {str(cpu.p)}
            """)

    @property
    def cpu(self) -> CPU:
        """Get the cpu."""
        return self.system.cpu

    @property
    def memory(self) -> MemoryMap:
        """Get the memory."""
        return self.system.memory

    def step(self, poll_hardware: bool = False) -> int:
        """
        Execute one instruction, optionally polling hardware.

        Return the instruction cycle time.
        """
        return self.system.step(poll_hardware)

    def run_for(self, upto: int) -> Metrics | None:
        """
        Run for at most 'upto' instructions.

        Returns a Metrics object or None.
        """
        return self.system.run_for(upto)

    def run(self) -> None:
        """
        Start the runtime.

        Start the cpu's run loop, print runtime metrics if they are returned. Handle CPUTrap exception.
        """
        try:
            res = self.system.run()
            print("\nExecution stopped.")
            if res:
                print(res)
        except CPUTrap as trap:
            self._trap_handler(trap.cpu)


class TuiRuntime(Runtime):
    """Terminal backed runtime class."""

    def __init__(self, config: Dynaconf) -> None:
        """Create a tui backed runtime."""
        self.console = tui.ConsoleWidget(id="console")
        self.system = AppleOne(display_backend=tui.TuiDisplayBackend(self.console), keyboard_backend=tui.TuiKeyboardBackend(self.console), config=config)
        self.ui = tui.UI(self)
        self._runnable = False
        self._metrics: Metrics | None = None

    def _trap_handler(self, cpu: CPU) -> None:
        pass

    @property
    def cpu(self) -> CPU:
        """Get the cpu."""
        return self.system.cpu

    @property
    def memory(self) -> MemoryMap:
        """Get the memory."""
        return self.system.memory

    @property
    def metrics(self) -> Metrics:
        """Property for metrics attribute."""
        if self._metrics:
            return self._metrics
        else:
            return Metrics(0, 0, 0, 0, 0.0)

    def step(self, poll_hardware: bool = False) -> int:
        """
        Execute one instruction, optionally polling hardware.

        Return the instruction cycle time.
        """
        return self.system.step(poll_hardware)

    def run_for(self, upto: int) -> Metrics | None:
        """
        Run for at most 'upto' instructions.

        Returns a Metrics object or None.
        """
        if self._runnable:
            res = self.system.run_for(upto)
            if res:
                self._metrics = self._metrics + res

    def run(self) -> None:
        """Start the runtime,in this runtime we just start the ui event loop."""
        self._runnable = True
        self.ui.run()

    def stop(self) -> None:
        """Stop runtime."""
        self._runnable = False
        self.console.stop()

    def resume(self) -> None:
        """Resume emulator."""
        self._runnable = True
        self.console.resume()
