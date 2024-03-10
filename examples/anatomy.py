"""An example to convert images of notes of an anatomy and physiology textbook into digital form."""

import configmate
import os
import fire
import tqdm

from papyrusai import models, reading, writing


def main(input_folder: os.PathLike, output_folder: os.PathLike) -> None:
    for path in tqdm.tqdm(os.listdir(input_folder)):
        if not path.endswith(("jpg", "png", "jpeg")):
            continue
        fullpath = os.path.join(input_folder, path)
        output_fn = f"output_{path.split('.')[0]}.txt"
        output_path = os.path.join(output_folder, output_fn)
        if output_fn in os.listdir(output_folder):
            continue
        convert_image_from_path(fullpath, output_path)


def convert_image_from_path(image_path: os.PathLike, save_path: os.PathLike) -> None:
    config = configmate.get_config(
        "config/anatomy.yaml",
        section="AnatomyAndPhysiologyTextbook",
        validation=models.ImageToTextPrompt,
    )
    writer = writing.FileWriter(save_path)
    reader = reading.GPTImageReader(image_path, config.prompt())
    writer.write(reader.read())


if __name__ == "__main__":
    fire.Fire(main)
