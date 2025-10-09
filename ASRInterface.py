from typing import List

from TranscribedPhrase import TranscribedPhrase


class ASRInterface:
    def speechToText(self, filepath, prompt, language) -> List[TranscribedPhrase]:
        pass