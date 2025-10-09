from dataclasses import dataclass
from typing import Optional


@dataclass
class TranscribedPhrase:
    start: Optional[float] = None
    end: Optional[float] = None
    text: str = ""
    translatedText: str = ""
