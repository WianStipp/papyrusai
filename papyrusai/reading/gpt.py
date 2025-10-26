"""This module contains code to read from image / input to an intermediate form."""

from typing import Any
import os
import requests

from papyrusai.reading import base


class GPTImageReader(base.Reader):
    def __init__(
        self,
        path_to_image: os.PathLike,
        prompt: str,
        heic_output_format: str = "png",
        model_name: str = "gpt-5",
    ) -> None:
        super().__init__()
        self.prompt = prompt
        self.model_name = model_name
        self._heic_output_format = heic_output_format.lower()
        self._encoded_image, self._mime_type = self.encode_image(path_to_image)

    def read(self) -> str:
        payload = self._get_payload()
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=self._get_headers(),
            json=payload,
        )
        try:
            response.raise_for_status()
        except Exception as e:
            print(response.content)
            raise e
        return response.json()["choices"][0]["message"]["content"]

    def _get_payload(self) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{self._mime_type};base64,{self._encoded_image}"
                            },
                        },
                    ],
                }
            ],
            "max_completion_tokens": 5096,
        }

    @staticmethod
    def _get_headers() -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        }
