from typing import List

import pysrt

from ASRInterface import ASRInterface
from TranscribedPhrase import TranscribedPhrase


class ASRFromSrtFile(ASRInterface):
    def speechToText(self, filepath, prompt = None, language = None) -> List[TranscribedPhrase]:
        srtLines = pysrt.open(filepath, encoding="utf-8")

        phrases = []

        for line in srtLines:
            start = line.start.ordinal / 1000.0
            end = line.end.ordinal / 1000.0
            phrases.append(TranscribedPhrase(start, end, line.text))

        return phrases