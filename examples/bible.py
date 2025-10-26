"""An example to convert images of notes of an anatomy and physiology textbook into digital form."""

import configmate
import os
import fire

from papyrusai import converting, models


def main(input_folder: os.PathLike, output_folder: os.PathLike) -> None:
    config = configmate.get_config(
        "config/bible.yaml",
        section="TheBible",
        validation=models.ImageToTextPrompt,
    )
    converting.run_on_folder_sync(config, input_folder, output_folder)


if __name__ == "__main__":
    fire.Fire(main)
