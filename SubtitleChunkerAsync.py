from collections import deque
from functools import reduce

from MessageBus import MessageType
from TranscribedPhrase import TranscribedPhrase


class SubtitleChunker:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.words = []
        self.bufferSize = 0

        self.bus.subscribe(MessageType.ASR_FINAL)(self.onASRWord)

    async def onASRWord(self, data):
        # print(f"Received async message: {data}")
        self.words.append(data)
        self.bufferSize += len(data.text)

        if self.shouldChunk():
            phrase = TranscribedPhrase(
                start=self.words[0].start,
                end=self.words[-1].end,
                text="".join([word.text for word in self.words])
            )
            self.bus.publish(MessageType.SUBTITLE_CHUNK, phrase)
            # print(f"Chunker published {phrase.text}")
            self.words = []
            self.bufferSize = 0

    def shouldChunk(self):
        """
        Chunking strategy - turning a stream of words into subtitle lines
        - Always break line on end of sentence punctuation
        - If within target line length, break if silence is over threshold
        - If beyond target line length, break if silence is over short threshold, or if word is longer than threshold
        - If at max line length, forcibly break
        """

        if not len(self.words):
            return False

        delimiters = {"。", "？", "?"}

        # return True

        return reduce(lambda acc, delimiter: acc or delimiter in self.words[-1].text, delimiters, False)

        # if self.words[-1].text.contains()
        #
        # if self.bufferSize < 30:
