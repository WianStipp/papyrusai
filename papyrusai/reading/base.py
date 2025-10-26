from typing import Any
import abc
import os
import base64
import mimetypes
import io
import subprocess
import tempfile
import pathlib
import shutil

try:
    import pillow_heif  # type: ignore
    from PIL import Image, UnidentifiedImageError  # type: ignore
except ImportError:  # pragma: no cover - optional dependency guard
    pillow_heif = None  # type: ignore
    Image = None  # type: ignore
    UnidentifiedImageError = Exception  # type: ignore


_HEIC_EXTENSIONS = {".heic", ".heif"}
_HEIC_OUTPUT_FORMATS = {
    "png": ("PNG", "image/png"),
    "jpeg": ("JPEG", "image/jpeg"),
    "jpg": ("JPEG", "image/jpeg"),
    "webp": ("WEBP", "image/webp"),
    "gif": ("GIF", "image/gif"),
}


class Reader(abc.ABC):
    _heic_output_format = "png"

    @abc.abstractmethod
    def read(self) -> str: ...

    def encode_image(self, path_to_image: os.PathLike | str) -> tuple[str, str]:
        raw_bytes, mime_type = self._load_image_bytes(path_to_image)
        encoded = base64.b64encode(raw_bytes).decode("utf-8")
        return encoded, mime_type

    def _load_image_bytes(self, path_to_image: os.PathLike | str) -> tuple[bytes, str]:
        extension = os.path.splitext(path_to_image)[1].lower()
        if extension in _HEIC_EXTENSIONS:
            return self._convert_heic_image(path_to_image)
        with open(path_to_image, "rb") as f:
            return f.read(), self._guess_mime_type(path_to_image)

    def _convert_heic_image(
        self, path_to_image: os.PathLike | str
    ) -> tuple[bytes, str]:
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
        image = self._load_heic_as_pillow_image(path_to_image)

        if format_name in {"JPEG", "WEBP"}:
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
        elif format_name == "GIF":
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            image = image.convert("P", palette=Image.ADAPTIVE)

        buffer = io.BytesIO()
        save_kwargs: dict[str, Any] = {"format": format_name}
        if format_name == "JPEG":
            save_kwargs["quality"] = 95
            save_kwargs["optimize"] = True
        if format_name == "WEBP":
            save_kwargs["quality"] = 95
        image.save(buffer, **save_kwargs)
        return buffer.getvalue(), mime_type

    def _load_heic_as_pillow_image(
        self, path_to_image: os.PathLike | str
    ) -> "Image.Image":
        """Load a HEIC/HEIF image into a Pillow Image, with resilient fallbacks."""
        path = os.fspath(path_to_image)
        attempts: list[str] = []

        def _try_open(**kwargs: Any) -> "Image.Image | None":
            try:
                heif_file = pillow_heif.open_heif(
                    path, convert_hdr_to_8bit=True, **kwargs
                )
                return heif_file.to_pillow()
            except ValueError as exc:
                if "Metadata not correctly assigned" not in str(exc):
                    raise
                attempts.append(str(exc))
            except Exception as exc:
                attempts.append(str(exc))
            return None

        image = _try_open()
        if image is not None:
            return image

        image = _try_open(reload_size=True)
        if image is not None:
            return image

        try:
            heif_file = pillow_heif.read_heif(path, convert_hdr_to_8bit=True)
            return heif_file.to_pillow()
        except Exception as exc:
            attempts.append(str(exc))

        # Temporarily allow incorrect headers at the options level to let Pillow plugin decode.
        original_allow_incorrect = getattr(
            pillow_heif.options, "ALLOW_INCORRECT_HEADERS", False
        )
        pillow_heif.options.ALLOW_INCORRECT_HEADERS = True
        try:
            pillow_heif.register_heif_opener(allow_incorrect_headers=True)
            with Image.open(path) as img:
                return img.copy()
        except (UnidentifiedImageError, ValueError) as exc:
            attempts.append(str(exc))
        except Exception as exc:
            attempts.append(str(exc))
        finally:
            pillow_heif.options.ALLOW_INCORRECT_HEADERS = original_allow_incorrect

        message = "; ".join({msg for msg in attempts if msg})

        external_image = self._convert_heic_with_external_tool(path, attempts)
        if external_image is not None:
            return external_image

        raise RuntimeError(
            f"Failed to decode HEIC image '{path}' after multiple attempts."
            + (f" Details: {message}" if message else "")
        )

    def _convert_heic_with_external_tool(
        self, path: str, attempts: list[str]
    ) -> "Image.Image | None":
        """Fallback conversion using OS utilities when Python decoders fail."""
        converters = []
        if shutil.which("magick"):
            converters.append(self._convert_with_magick)
        if shutil.which("sips"):
            converters.append(self._convert_with_sips)

        for converter in converters:
            try:
                return converter(path)
            except Exception as exc:  # pragma: no cover - depends on host tools
                attempts.append(str(exc))
        return None

    @staticmethod
    def _convert_with_magick(path: str) -> "Image.Image":
        """Use ImageMagick to convert HEIC to PNG via stdout."""
        result = subprocess.run(
            ["magick", path, "png:-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        buffer = io.BytesIO(result.stdout)
        with Image.open(buffer) as img:
            return img.copy()

    @staticmethod
    def _convert_with_sips(path: str) -> "Image.Image":
        """Use macOS sips utility to convert HEIC to PNG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = pathlib.Path(tmpdir) / "converted.png"
            subprocess.run(
                ["sips", "-s", "format", "png", path, "--out", str(output_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            with Image.open(output_path) as img:
                return img.copy()

    @staticmethod
    def _guess_mime_type(path_to_image: os.PathLike | str) -> str:
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
