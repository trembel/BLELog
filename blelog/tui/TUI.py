from abc import ABC, abstractmethod
import logging
from typing import List
import asyncio
from asyncio import Event

from blelog.Configuration import Configuration


class TUIComponent(ABC):
    @abstractmethod
    def get_lines(self) -> List[str]:
        pass

    @abstractmethod
    def title(self) -> str:
        pass


class TUI():
    def __init__(self, components: List[TUIComponent], config: Configuration) -> None:
        self.config = config
        self.last_update = None
        self.components = components

    async def run(self, halt: Event) -> None:
        log = logging.getLogger('log')
        try:
            while not halt.is_set():
                print("\r\n" * 20)
                for c in self.components:
                    print('\r\n    ========== %s =========\r\n' % c.title())
                    for line in c.get_lines():
                        print(line)

                await asyncio.sleep(self.config.tui_interval)
        except Exception as e:
            log.error('TUI encountered an exception: %s' % str(e))
            halt.set()
        finally:
            print('TUI Shutdown...')

