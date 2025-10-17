from MessageBus import MessageType


class SomePrinter:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.bus.subscribe(MessageType.ASR_FINAL)(self.onASRFinal)
        self.bus.subscribe(MessageType.SUBTITLE_CHUNK)(self.onSubtitleChunk)

    async def onASRFinal(self, data):
        print(f"{data.text}", end="")

    async def onSubtitleChunk(self, data):
        print("\n", end="")