from typing import List

from openai.types import ResponsesModel

from TranscribedPhrase import TranscribedPhrase


class TranslationInterface:
    def translate(self, phrases: List[TranscribedPhrase], extraPrompts, model: ResponsesModel) -> None:
        pass