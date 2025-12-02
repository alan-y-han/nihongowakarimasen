from collections import deque
from functools import reduce

from AsyncUtils import serialSubscriber
from MessageBus import MessageType
from TranscribedPhrase import SubtitleChunk


class SubtitleChunker:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.words = []
        self.bufferSize = 0
        self.phraseId = 0

        serialSubscriber(self.bus, MessageType.ASR_FINAL)(self.onASRWord)

        # self.bus.subscribe(MessageType.ASR_FINAL)(self.onASRWord)

    async def onASRWord(self, data):
        # print(f"Received async message: {data}")
        self.words.append(data)
        self.bufferSize += len(data.text)

        if self.shouldChunk():
            subtitleChunk = SubtitleChunk(
                start=self.words[0].start,
                end=self.words[-1].end,
                text="".join([word.text for word in self.words]),
                uuid=str(self.phraseId)
            )
            self.bus.publish(MessageType.SUBTITLE_CHUNK, subtitleChunk)
            # print(f"Chunker published {subtitleChunk.text}")
            self.words = []
            self.bufferSize = 0
            self.phraseId += 1

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

        return reduce(lambda acc, delimiter: acc or delimiter in self.words[-1].text, delimiters, False)

        # return True
