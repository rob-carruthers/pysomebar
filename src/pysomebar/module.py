import datetime
from abc import ABC, abstractmethod

from .config import CONFIG


class Module(ABC):
    def __init__(self, interval: int) -> None:
        self.interval = interval
        self.output: str = ""

    @abstractmethod
    def update(self) -> None: ...


class DateModule(Module):
    def __init__(self, interval: int):
        super().__init__(interval)

    def update(self) -> None:
        now = datetime.datetime.now().astimezone().strftime(CONFIG.date.format)
        self.output = now
