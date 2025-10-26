"""General script to convert a folder of images to a folder of texts."""

import asyncio
import os
import tqdm

from papyrusai import models, reading, writing


async def run_on_folder(
    promptable: models.Promptable,
    input_folder: os.PathLike,
    output_folder: os.PathLike,
    max_concurrency: int | None = 5,
) -> None:
    """Convert every supported image in a folder concurrently.

    Parameters
    ----------
    promptable:
        Provides the prompt that is sent to the image-to-text model.
    input_folder / output_folder:
        Source directory with images and destination directory for text files.
    heic_output_format:
        Optional override for HEIC/HEIF conversion targets.
    max_concurrency:
        Maximum number of in-flight conversions. ``None`` disables throttling.
    """
    os.makedirs(output_folder, exist_ok=True)
    supported_extensions = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
    existing_outputs = set(os.listdir(output_folder))
    semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency else None

    async def _process(path: str) -> None:
        if semaphore:
            async with semaphore:
                await _convert_path(path)
        else:
            await _convert_path(path)

    async def _convert_path(path: str) -> None:
        fullpath = os.path.join(input_folder, path)
        output_fn = f"output_{path.split('.')[0]}.txt"
        output_path = os.path.join(output_folder, output_fn)
        await asyncio.to_thread(
            convert_image_from_path,
            promptable,
            fullpath,
            output_path,
        )

    tasks = []
    for path in sorted(os.listdir(input_folder)):
        _, extension = os.path.splitext(path)
        if extension.lower() not in supported_extensions:
            continue
        output_fn = f"output_{path.split('.')[0]}.txt"
        if output_fn in existing_outputs:
            continue
        existing_outputs.add(output_fn)
        tasks.append(asyncio.create_task(_process(path)))

    if not tasks:
        return

    for task in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
        await task


def run_on_folder_sync(
    promptable: models.Promptable,
    input_folder: os.PathLike,
    output_folder: os.PathLike,
    max_concurrency: int | None = 5,
) -> None:
    """Blocking wrapper around :func:`run_on_folder`."""
    asyncio.run(
        run_on_folder(
            promptable,
            input_folder,
            output_folder,
            max_concurrency=max_concurrency,
        )
    )


def convert_image_from_path(
    promptable: models.Promptable,
    image_path: os.PathLike,
    save_path: os.PathLike,
) -> None:
    writer = writing.FileWriter(save_path)
    reader = reading.MistralOCRReader(promptable.prompt(), image_path)
    writer.write(reader.read())
