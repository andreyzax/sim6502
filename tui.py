"""Common tui widgets."""

from collections import deque
from math import ceil
from typing import Callable

import textual.events as events
from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult, RenderResult
from textual.containers import Horizontal
from textual.events import Key
from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Button

from memory import ADDRESS_SPACE_SIZE, MemoryMap


class ConsoleWidget(Widget):
    """
    A textual tui widget that models an Apple 1 console.

    Used by the tui hardware backends and embedded inside the tui runtime shell.
    """

    can_focus = True

    def __init__(self, max_lines=500, *args, **kwargs):
        """
        Initialize the console.

        Accepts max_lines to set scrollback buffer size. Also accepts any generic
        textual Widget arguments (id, class,...)
        """
        super().__init__(*args, **kwargs)

        self._lines: deque[str] = deque(maxlen=max_lines)
        self._inject_char: Callable[[str], None] | None = None
        self._dirty = False
        self._cursor = Text("@", style="blink")

        self.border_title = "Console"

    def flush(self) -> None:
        """
        Sync visible console content with internal buffer.

        Writes to the console won't be shown on screen without calling this.
        """
        if self._dirty:
            self.refresh()
            self._dirty = False

    @property
    def inject_char(self) -> Callable[[str], None] | None:
        """inject_char property."""
        return self._inject_char

    @inject_char.setter
    def inject_char(self, value: Callable[[str], None]) -> None:
        """
        inject_char setter.

        This property is a callable which accepts a one char string and is responsible
        to pass console input to the emulated keyboard interface.
        """
        self._inject_char = value

    def display_char(self, char: str) -> None:
        """
        Add a character to the console buffer, handles new line processing.

        This method will not display the new output immediately, flush() must be called
        to sync the internal buffer with the rendered text.
        """
        if char == "\n":
            self._lines.append("")
        else:
            self._lines[-1] += char

        self._dirty = True

    def on_key(self, event: Key) -> None:
        """
        Respond to textual keyboard input events and inject them to the emulated keyboard interface.

        Handles carriage return (enter key) and control character processing.
        """
        if self.inject_char:  # we could be called without a set self.inject_char, need to guard against that.
            if event.is_printable:
                assert event.character is not None
                self.inject_char(event.character)
            if event.name == "enter":
                self.inject_char("\n")
            if event.name in ("ctrl_r", "ctrl_d"):
                assert event.character is not None
                self.inject_char(event.character)
        else:
            pass  # Since we don't have a way to pass input to the emulator, we just do nothing

    def render(self) -> RenderResult:
        """
        Render the console buffer into the widget content area.

        Only renders the visible part of the buffer.
        """
        height = max(1, self.content_size.height)
        nlines = len(self._lines)
        visible = nlines - height
        if height == 0:
            return ""

        content = "\n".join([line for line_number, line in enumerate(self._lines) if line_number >= visible])
        return Text(content) + self._cursor

    def stop(self) -> None:
        """
        Stops the console.

        Currently this only stops the cursor blink.
        """
        self._cursor = Text("@", style="")
        self.refresh()

    def resume(self) -> None:
        """
        Resume the console.

        Currently, just resumes the cursor blink.
        """
        self._cursor = Text("@", style="blink")
        self.refresh()


class HelpBar(Horizontal):
    """
    Displays application global key bindings.

    The bindings are also clickable buttons.
    """

    def __init__(self) -> None:
        """
        Init base class and provide sensible default styles.

        Avoid overriding these in a tcss file if possible.
        The widget is really intended to be used with these styles.
        Adding additional styles (color, background,...) is fine.
        """
        super().__init__()
        self.styles.width = "100%"
        self.styles.height = "auto"
        self.styles.dock = "top"
        self.can_focus = False

    def compose(self) -> ComposeResult:
        """Create and assemble the widget's sub widgets."""
        for key, command in self.app.active_bindings.items():
            if command.binding.show:
                btn = Button(label=f"{key.upper()}: {command.binding.description}", compact=True, action=f"app.{command.binding.action}", classes="help-button")
                btn.can_focus = False
                yield btn


class MemoryViewer(ScrollView):
    """
    Memory view widget.

    Scrollable and supports automatic content reflow on resize.
    """

    def __init__(self, memory: MemoryMap):
        """Init base class and store memory map reference."""
        super().__init__()
        self.mm = memory

    def on_mount(self) -> None:
        """Calculate self.virtual_size data row width (nbytes) based on content width after layout."""
        self.nbytes = max(1, (self.content_size.width - 6) // 3)  # 3 chars per byte "_XX"
        self.virtual_size = Size(self.content_size.width, ceil(ADDRESS_SPACE_SIZE / self.nbytes))

    def on_resize(self, event: events.Resize) -> None:
        """Update self.virtual_size and data row width (nbytes) after resize events."""
        self.nbytes = max(1, (self.content_size.width - 6) // 3)
        self.virtual_size = Size(self.content_size.width, ceil(ADDRESS_SPACE_SIZE / self.nbytes))

    def render_line(self, y: int) -> Strip:
        """Render content line based based on data row address and width."""
        virtual_line = round(self.scroll_offset.y) + y
        address = virtual_line * self.nbytes
        data = self.mm[address : address + self.nbytes]
        data_str = " ".join(f"{byte:02X}" for byte in data)

        if address >= ADDRESS_SPACE_SIZE:
            return Strip.blank(self.size.width)

        return Strip((Segment(f"{address:04X}: {data_str}", style=Style(bgcolor="#008080", color="white", bold=True)),))
