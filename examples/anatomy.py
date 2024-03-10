"""An example to convert images of notes of an anatomy and physiology textbook into digital form."""

import configmate
import os
import fire

from papyrusai import models, reading


def main(image_path: os.PathLike) -> None:
    config = configmate.get_config(
        "config/anatomy.yaml",
        section="AnatomyAndPhysiologyTextbook",
        validation=models.ImageToTextPrompt,
    )
    reader = reading.GPTImageReader(image_path, config.prompt())
    print(reader.read())


if __name__ == "__main__":
    fire.Fire(main)
