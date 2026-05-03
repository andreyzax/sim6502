"""
Global configuration module.

Contains variables that are consumed by other modules.
Setting these values should be done by dedicated configuration importer code.
Here are only be variables with default values. Also please note that these are *variables*
not constants! They are defined with lower case names and the values here are only default values.
"""

enable_runtime_perf_metrics: bool = False
trap_brk: bool = False

terminal_device = None
backend = "terminal"

roms = ((0xFF00, "bin/wozmon.bin"), (0xE000, "bin/basic.bin"))

program = (0x280, "bin/mandelbrot-65.bin", "rb")
