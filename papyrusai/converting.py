"""General script to convert a folder of images to a folder of texts."""

import os
import tqdm

from papyrusai import models, reading, writing


def run_on_folder(
    promptable: models.Promptable,
    input_folder: os.PathLike,
    output_folder: os.PathLike,
) -> None:
    os.makedirs(output_folder, exist_ok=True)
    for path in tqdm.tqdm(sorted(os.listdir(input_folder))):
        if not path.endswith(("jpg", "png", "jpeg")):
            continue
        fullpath = os.path.join(input_folder, path)
        output_fn = f"output_{path.split('.')[0]}.txt"
        output_path = os.path.join(output_folder, output_fn)
        if output_fn in os.listdir(output_folder):
            continue
        convert_image_from_path(promptable, fullpath, output_path)


def convert_image_from_path(
    promptable: models.Promptable, image_path: os.PathLike, save_path: os.PathLike
) -> None:
    writer = writing.FileWriter(save_path)
    reader = reading.GPTImageReader(image_path, promptable.prompt())
    writer.write(reader.read())
