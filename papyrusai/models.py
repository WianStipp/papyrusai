"""Module containing data models."""

from typing import Optional
import abc
import pydantic


class Promptable(abc.ABC):
    @abc.abstractmethod
    def prompt(self) -> str: ...


class ImageToTextPrompt(pydantic.BaseModel, Promptable):
    instruction: str
    topic: Optional[str] = None

    def prompt(self) -> str:
        prompt = self.instruction
        if self.topic is not None:
            prompt = f"For context, the topic is: {self.topic}.\n\n{prompt}"
        return prompt
