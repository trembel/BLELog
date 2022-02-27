import asyncio
import curses
import logging
from abc import ABC, abstractmethod
from asyncio import Event
from asyncio.queues import Queue
from collections import deque
from typing import Callable, List

from blelog.Configuration import Configuration, TUI_Mode


class LogHandler(logging.Handler):
    def __init__(self, output: deque):
        super().__init__()
        self.out = output

    def handle(self, record: logging.LogRecord) -> bool:
        self.out.append(record)
        return True


class AsyncLogHandler(logging.Handler):
    def __init__(self, output: Queue):
        super().__init__()
        self.out = output

    def handle(self, record: logging.LogRecord) -> bool:
        self.out.put_nowait(record)
        return True


class CursesTUI_Component(ABC):
    @abstractmethod
    def get_lines(self) -> List[str]:
        pass

    @abstractmethod
    def title(self) -> str:
        pass


class TUI:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.components = []
        self.curse_stdscr = None
        self.cures_is_initialised = False
        self.curse_is_shutoff = False
        self.halt_hndlr = None
        # Setup log handler for CONSOLE mode:
        self.console_q = Queue()
        self.console_lh = AsyncLogHandler(self.console_q)
        self.console_lh.setLevel(logging.INFO)
        logging.getLogger('log').addHandler(self.console_lh)

    def add_component(self, c: CursesTUI_Component) -> None:
        self.components.append(c)

    def set_halt_handler(self, hndlr) -> None:
        self.halt_hndlr = hndlr

    async def run(self, halt: Event) -> None:
        if self.config.tui_mode == TUI_Mode.CURSE:
            await self.run_curses(halt)
        else:
            await self.run_console(halt)

    async def run_console(self, halt: Event) -> None:
        log = logging.getLogger('log')
        try:

            if self.config.plain_ascii_tui:
                icons = {
                    'INFO': '    ',
                    'WARNING': 'WARN',
                    'ERROR': 'ERR '
                }
            else:
                icons = {
                    'INFO': 'ℹ️',
                    'WARNING': '⚠️',
                    'ERROR': '‼️'
                }

            print("==== BLELOG ====")

            while not halt.is_set():
                try:
                    i = await asyncio.wait_for(self.console_q.get(), timeout=0.5)
                    print(icons[i.levelname] + ' ' + i.getMessage())
                except asyncio.TimeoutError:
                    pass

        except Exception as e:
            log.error('TUI encountered an exception: %s' % str(e))
            halt.set()
        finally:
            print('TUI Shutdown...')

    async def run_curses(self, halt: Event) -> None:
        log = logging.getLogger('log')
        try:
            self.cures_is_initialised = True
            stdscr = curses.initscr()
            self.curse_stdscr = stdscr
            curses.noecho()
            curses.cbreak()
            stdscr.keypad(True)

            while not halt.is_set():
                # Header:
                lines = []
                lines.append('========== BLELOG =========')
                lines.append('')
                lines.append('\'g\': Toggle GUI Plot')
                lines.append('\'CTRL-C\': Close BLELog')
                lines.append('')

                # Get lines from each TUI component:
                for c in self.components:
                    lines.append('========== %s =========' % c.title())
                    lines.append('')
                    lines.extend(c.get_lines())
                    lines.append('')

                # Draw to screen
                stdscr.clear()
                max_rows, max_cols = stdscr.getmaxyx()

                for i, line in enumerate(lines):
                    if i >= max_rows:
                        break

                    # strip newlines:
                    line = line.replace('\n', '').replace('\r', '')

                    # truncate line:
                    line = (line[:max_cols-5] + '...') if len(line) > max_cols-5 else line
                    stdscr.addstr(i, 0, line)

                stdscr.refresh()

                # Handle input
                stdscr.nodelay(True)
                c = stdscr.getch()

                # Under windows, the SIGINT handler is not called automatically.
                # Manually call it:
                if c == 3:
                    if self.halt_hndlr is not None:
                        self.halt_hndlr()

                # Toggle plotter gui
                if c == ord('G') or c == ord('g'):
                    if self.plot_toggle is not None:
                        self.plot_toggle()

                await asyncio.sleep(self.config.curse_tui_interval)
        except Exception as e:
            log.error('TUI encountered an exception: %s' % str(e))
            halt.set()
        finally:
            self.off()
            print('TUI Shutdown...')

    def off(self) -> None:
        if self.cures_is_initialised and not self.curse_is_shutoff:
            curses.nocbreak()
            if self.curse_stdscr is not None:
                self.curse_stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            self.curse_is_shutoff = True

    def set_plot_toggle(self, plot_toggle: Callable):
        self.plot_toggle = plot_toggle
