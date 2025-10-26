"""This module contains code to output the extracted text into various outputs."""

import os
import abc


class Writer(abc.ABC):
    @abc.abstractmethod
    def write(self, content: str) -> None: ...


class FileWriter(Writer):
    def __init__(self, write_path: os.PathLike | str) -> None:
        super().__init__()
        self.write_path = write_path

    def write(self, content: str) -> None:
        with open(self.write_path, "w") as f:
            f.write(content)
