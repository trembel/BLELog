from abc import ABC, abstractmethod
from asyncio.queues import Queue
from collections import deque
import logging
from typing import List
import asyncio
from asyncio import Event

from blelog.Configuration import Configuration, TUI_Mode
import curses


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


class TUIComponent(ABC):
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

    def add_component(self, c: TUIComponent) -> None:
        self.components.append(c)

    async def run(self, halt: Event) -> None:
        if self.config.tui_mode == TUI_Mode.CURSE:
            await self.run_curses(halt)
        else:
            await self.run_console(halt)

    async def run_console(self, halt: Event) -> None:
        log = logging.getLogger('log')
        try:
            q = Queue()
            lh = AsyncLogHandler(q)
            lh.setLevel(logging.INFO)
            log.addHandler(lh)

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

            while not halt.is_set():
                try:
                    i = await asyncio.wait_for(q.get(), timeout=0.5)
                    print(icons[i.levelname] + ' ' + i.msg)
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
                # Get lines from each TUI component:
                lines = []
                for c in self.components:
                    lines.append('========== %s =========' % c.title())
                    lines.append('')
                    lines.extend(c.get_lines())
                    lines.append('')

                # Draw to screen
                stdscr.clear()
                for i, line in enumerate(lines):
                    stdscr.addstr(i, 0, line)
                stdscr.refresh()

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
