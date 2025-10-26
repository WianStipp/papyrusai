import os
import mistralai

from papyrusai.reading import base


class MistralOCRReader(base.Reader):
    def __init__(self, prompt: str, path_to_image: os.PathLike | str) -> None:
        self.prompt = prompt
        self._encoded_image, self._mime_type = self.encode_image(path_to_image)
        self._client = mistralai.Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    def read(self) -> str:
        response = self._client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": f"data:{self._mime_type};base64,{self._encoded_image}",
            },
            include_image_base64=True,
        )
        markdown = "\n\n".join(p.markdown for p in response.pages)
        prompt = f"{self.prompt}\n\n======================\n\nNow the part I'd like to convert: {markdown}"
        chat_response = self._client.chat.complete(
            model="mistral-medium-latest",
            messages=[{"role": "user", "content": prompt}],
        )
        chat_content = chat_response.choices[0].message.content
        assert isinstance(chat_content, str)
        return chat_content
