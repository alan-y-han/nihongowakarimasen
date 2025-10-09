import io
from typing import List

from openai import OpenAI
from pydub import AudioSegment

from Logger import logger
from ASRInterface import ASRInterface
from TranscribedPhrase import TranscribedPhrase


class ASROpenAIWhisper(ASRInterface):
    def speechToText(self, filepath, prompt, language) -> List[TranscribedPhrase]:
        audioBuffer = io.BytesIO()
        audioBuffer.name = "timetosimp.webm"  # dummy file name so openai doesn't throw errors

        endOfFile = False
        startTimeSeconds = 0
        transcriptAllLines = []

        while not endOfFile:
            # clear the buffer to save memory
            audioBuffer.seek(0)
            audioBuffer.truncate(0)

            endTimeSeconds, endOfFile = chunkAudio24MB(filepath, audioBuffer, startTimeSeconds)
            logger.info(f"Transcribing audio: {startTimeSeconds}s to {endTimeSeconds}s")
            rawTranscript = getTranscript(audioBuffer, prompt, language)
            transcriptLines = chunkTranscription(rawTranscript, startTimeSeconds)

            if len(transcriptLines):
                if endTimeSeconds - transcriptLines[-1].end > lineSplitTimeThreshold:
                    # audio didn't cut mid-sentence
                    transcriptAllLines.extend(transcriptLines)

                    startTimeSeconds = endTimeSeconds
                    # add some time padding
                    if len(transcriptLines):
                        startTimeSeconds = max(startTimeSeconds - 0.2, transcriptLines[-1].end)
                else:
                    # audio cut sentence in half, re-transcribe from the beginning of that sentence

                    # handles edge case where there is only one chunk and it occupies the whole 30 seconds
                    # otherwise we will endlessly loop that 30secs (until we run out of openai credit)
                    # use 1 second threshold to detect this
                    if len(transcriptLines) == 1 and (startTimeSeconds - transcriptLines[0].start) < 1:
                        transcriptAllLines.extend(transcriptLines)
                        startTimeSeconds = transcriptLines[0].end
                    else:
                        transcriptAllLines.extend(
                            transcriptLines[:-1])  # add lines except the last line which got cut off

                        startTimeSeconds = transcriptLines[-1].start  # continue from the beginning of the last line
                        # add some time padding
                        if len(transcriptLines) >= 2:
                            startTimeSeconds = max(startTimeSeconds - 0.2, transcriptLines[-2].end)
            else:
                # no speech detected, move to next audio segment
                startTimeSeconds = endTimeSeconds

        return transcriptAllLines


def chunkAudio24MB(filepath, newFileBuffer, startTimeSeconds):
    logger.info("Generating webm audio")

    audio = AudioSegment.from_file(filepath)
    bitrate = 256
    chunkTimeSeconds = 24 * 8 * (1024 / bitrate) # create 24MB of audio
    endTimeSeconds = startTimeSeconds + chunkTimeSeconds

    # PyDub handles time in milliseconds
    startTimeMs = startTimeSeconds * 1000
    endTimeMs = min(len(audio), endTimeSeconds * 1000) # this index might be beyond the end of the list - this is ok because it's python
    audioChunk = audio[startTimeMs:endTimeMs]
    audioChunk.export(newFileBuffer, format="webm", bitrate=f"{bitrate}k", codec="libopus")
    newFileBuffer.seek(0)

    return endTimeSeconds, endTimeMs == len(audio)


def getTranscript(audioFile, prompt, language):
    client = OpenAI()
    return client.audio.transcriptions.create(
        file=audioFile,
        language=language,
        model="whisper-1",
        prompt=prompt,
        response_format="verbose_json",
        timestamp_granularities = ["word"]
    )


lineSplitTimeThreshold = 0.35 # any gaps longer than this will create a new subtitle line

def chunkTranscription(transcription, timeOffsetSeconds):
    class PhraseBuffer:
        phrases = []

        start = None
        end = None
        textBuffer = []

        def flush(self):
            self.phrases.append(TranscribedPhrase(self.start + timeOffsetSeconds, self.end + timeOffsetSeconds, "".join(self.textBuffer)))

            self.start = None
            self.end = None
            self.textBuffer = []

            # print(f"[word],FLUSH,FLUSH,FLUSH")

        def addWord(self, word):
            self.textBuffer.append(word.word)
            if self.start is None: self.start = word.start
            self.end = word.end

            # print(f"[word],{word.start},{word.end},{word.word}")

    phraseBuffer = PhraseBuffer()

    # TODO different languages have different punctuation, either swap delimiter characters or remove this feature entirely
    toBreakOn = {"。", "？", "?"}

    # filter out empty words
    filteredWords = [word for word in transcription.words if word.word]

    for i in range(len(filteredWords)):
        word = filteredWords[i]

        # add word to chunk
        phraseBuffer.addWord(word)

        # if this is not the last word
        if (i + 1) < len(filteredWords):
            nextWord = filteredWords[i + 1]

            if word.word[-1] in toBreakOn:
                phraseBuffer.flush()
                continue

            timeDifference = nextWord.start - word.end
            if timeDifference > lineSplitTimeThreshold:
                phraseBuffer.flush()
                continue
        else: # this is the last word
            phraseBuffer.flush()

    for phrase in phraseBuffer.phrases:
        logger.info(f"[{phrase.start:.1f} - {phrase.end:.1f}] {phrase.text}")
    logger.info("--- transcription segment end ---")

    return phraseBuffer.phrases
