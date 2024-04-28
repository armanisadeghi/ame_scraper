import abc
from typing import Any


class ScrapeUseCase(abc.ABC):
    @abc.abstractmethod
    def __init__(self, _: Any):
        pass

    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _preprocess(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _process(self):
        raise NotImplementedError
