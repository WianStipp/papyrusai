"""This module contains code to read from image / input to an intermediate form."""

from typing import Dict, Any, Tuple
import abc
import os
import requests
import base64
import mimetypes
import io

try:
    import pillow_heif  # type: ignore
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover - optional dependency guard
    pillow_heif = None  # type: ignore
    Image = None  # type: ignore


_HEIC_EXTENSIONS = {".heic", ".heif"}
_HEIC_OUTPUT_FORMATS = {
    "png": ("PNG", "image/png"),
    "jpeg": ("JPEG", "image/jpeg"),
    "jpg": ("JPEG", "image/jpeg"),
    "webp": ("WEBP", "image/webp"),
    "gif": ("GIF", "image/gif"),
}


class Reader(abc.ABC):
    @abc.abstractmethod
    def read(self) -> str: ...


class GPTImageReader(Reader):
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
        self._encoded_image, self._mime_type = self._encode_image(path_to_image)

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

    def _get_payload(self) -> Dict[str, Any]:
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
    def _get_headers() -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        }

    def _encode_image(self, path_to_image: os.PathLike) -> Tuple[str, str]:
        raw_bytes, mime_type = self._load_image_bytes(path_to_image)
        encoded = base64.b64encode(raw_bytes).decode("utf-8")
        return encoded, mime_type

    def _load_image_bytes(self, path_to_image: os.PathLike) -> Tuple[bytes, str]:
        extension = os.path.splitext(path_to_image)[1].lower()
        if extension in _HEIC_EXTENSIONS:
            return self._convert_heic_image(path_to_image)
        with open(path_to_image, "rb") as f:
            return f.read(), self._guess_mime_type(path_to_image)

    def _convert_heic_image(self, path_to_image: os.PathLike) -> Tuple[bytes, str]:
        if self._heic_output_format not in _HEIC_OUTPUT_FORMATS:
            raise ValueError(
                f"Unsupported HEIC conversion target '{self._heic_output_format}'. "
                f"Choose one of {sorted(_HEIC_OUTPUT_FORMATS.keys())}."
            )
        if pillow_heif is None or Image is None:
            raise RuntimeError(
                "HEIC conversion requires the optional dependencies 'pillow-heif' and 'Pillow'. "
                "Install them to convert HEIC/HEIF images."
            )

        format_name, mime_type = _HEIC_OUTPUT_FORMATS[self._heic_output_format]
        heif_file = pillow_heif.open_heif(
            os.fspath(path_to_image), convert_hdr_to_8bit=True
        )
        image = heif_file.to_pillow()

        if format_name in {"JPEG", "WEBP"}:
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
        elif format_name == "GIF":
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            image = image.convert("P", palette=Image.ADAPTIVE)

        buffer = io.BytesIO()
        save_kwargs: Dict[str, Any] = {"format": format_name}
        if format_name == "JPEG":
            save_kwargs["quality"] = 95
            save_kwargs["optimize"] = True
        if format_name == "WEBP":
            save_kwargs["quality"] = 95
        image.save(buffer, **save_kwargs)
        return buffer.getvalue(), mime_type

    @staticmethod
    def _guess_mime_type(path_to_image: os.PathLike) -> str:
        extension = os.path.splitext(path_to_image)[1].lower()
        custom_mapping = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".heic": "image/heic",
            ".heif": "image/heif",
        }
        if extension in custom_mapping:
            return custom_mapping[extension]
        guessed, _ = mimetypes.guess_type(path_to_image)
        return guessed or "application/octet-stream"
