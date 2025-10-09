import math
from typing import List

from TranscribedPhrase import TranscribedPhrase
from logger import logger


def writeSubtitles(subtitleLines: List[TranscribedPhrase], filepath):
    extendTime = 0.2  # how long to extend each subtitle line by

    srtFile = []

    for i, subtitleLine in enumerate(subtitleLines):
        if subtitleLine.start is None or subtitleLine.end is None:
            logger.warn("Writing subtitle, no start/end timestamp detected")
            continue

        line = []
        line.append(f"{i + 1}")

        # slightly extend the end time of each subtitle line for readability
        endTimestamp = subtitleLine.end
        if i < (len(subtitleLines) - 1): # if not the last subtitleLine
            endTimestamp = min(subtitleLine.end + extendTime, subtitleLines[i + 1].start)

        line.append(f"{genTimestamp(subtitleLine.start)} --> {genTimestamp(endTimestamp)}")
        line.append(f"{subtitleLine.translatedText}")
        srtFile.append("\n".join(line))

    output = "\n\n".join(srtFile)

    outputFile = open(filepath + ".srt", "w", encoding="utf-8")
    outputFile.write(output)
    outputFile.close()

    logger.info(output)

def genTimestamp(seconds):
    hours = math.floor(seconds / 3600)
    seconds %= 3600

    minutes = math.floor(seconds / 60)
    seconds %= 60

    milliseconds = round((seconds - math.floor(seconds)) * 1000)

    seconds = math.floor(seconds)

    return f"{hours:02d}:{minutes:02d}:{seconds:01d},{milliseconds:03d}"