# PapyrusAI

I like [handwritten notes](https://wianstipp.com/100-books), but I like Obsidian for [storing and connecting ideas](https://www.youtube.com/watch?v=hSTy_BInQs8).

This is a tool I use to turn handwritten notes into digitial documents by sending them through a vision LLM with a controlable prompt.

## Highlights
- Works with folders of `.jpg`, `.jpeg`, `.png`, `.heic`, or `.heif` images.
- Lets you define detailed extraction prompts (topic, formatting rules, etc.).
- Ships with ready-made examples for textbook note transcription.
- Outputs plain text files you can drop into Obsidian, Notion, etc.

## Prerequisites
- Python 3.10 or newer
- An OpenAI API key.
- Poetry (for dependency management) — or install requirements manually

Export your API key before running anything:

```bash
export OPENAI_API_KEY="sk-..."
```

## Install & Configure

```bash
poetry install
```

You can now run commands with `poetry run ...` or drop into a shell via `poetry shell`.

## Quick Start

Convert an entire folder of images using one of the provided prompts:

```bash
poetry run python examples/anatomy.py ./notes/raw ./notes/clean
```

What happens:
- Loads `config/anatomy.yaml` to build the `ImageToTextPrompt`.
- Reads every supported image in `./notes/raw`.
- Writes OpenAI’s transcription for each image to `./notes/clean/output_<image-name>.txt`.

Swap in `examples/psychology.py` to use the psychology prompt profile instead.

## Use the Library Directly

```python
from papyrusai import converting, models

prompt = models.ImageToTextPrompt(
    instruction="Transcribe my lecture notes exactly. Mark anything unclear as [missing-information].",
    topic="Cognitive psychology seminar",
)

converting.convert_image_from_path(
    prompt,             # anything that implements Promptable.prompt()
    "note-page.jpg",    # input image path
    "note-page.txt",    # where to write the transcription
)
```

For batch conversion you can call `converting.run_on_folder(prompt, input_dir, output_dir)`.

## Customize Prompts

Edit the YAML files under `config/` or add new sections to tailor formatting rules, topics, or safety instructions. Each file maps to a `models.ImageToTextPrompt`, so any fields on that model are available.

## Troubleshooting
- Make sure `OPENAI_API_KEY` is set; the request will fail without it.
- The vision model may occasionally misread handwriting — tweak the prompt to guide it (e.g., request LaTeX, add domain hints, or clarify ambiguous markings).

Happy digitizing!
