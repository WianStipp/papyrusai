"""This module contains code to read from image / input to an intermediate form."""

from typing import Dict, Any
import abc
import os
import requests
import base64


class Reader(abc.ABC):
    @abc.abstractmethod
    def read(self) -> str: ...


class GPTImageReader(Reader):
    def __init__(self, path_to_image: os.PathLike, prompt: str) -> None:
        super().__init__()
        self.prompt = prompt
        self._encoded_image = self._encode_image(path_to_image)

    def read(self) -> str:
        payload = self._get_payload()
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=self._get_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _get_payload(self) -> Dict[str, Any]:
        return {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{self._encoded_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 2048,
        }

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        }

    @staticmethod
    def _encode_image(path_to_image: os.PathLike) -> bytes:
        with open(path_to_image, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
