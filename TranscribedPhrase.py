from dataclasses import dataclass
from typing import Optional


@dataclass
class Word:
    start: float
    end: float
    text: str

# TODO: get rid of Optional[] types after cleaning up old files
# and get rid of default values
@dataclass
class TranscribedPhrase:
    start: Optional[float] = None
    end: Optional[float] = None
    text: str = ""
    translatedText: str = ""
    uuid: Optional[str] = None

@dataclass
class SubtitleChunk:
    start: float
    end: float
    text: str
    uuid: str

@dataclass
class TranslatedPhrase:
    text: str
    uuid: str