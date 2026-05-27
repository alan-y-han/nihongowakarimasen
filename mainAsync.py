import asyncio

from ASRMockAsync import ASRMock
from ASRSpeechmaticsAsync import ASRSpeechmatics
from MessageBus import MessageBus
from SomePrinter import SomePrinter
from SubtitleChunkerAsync import SubtitleChunker
from TranslationBatchChatGPTAsync import TranslationBatchChatGPT


async def main():
    bus = MessageBus()

    asr = ASRSpeechmatics(bus)
    # asr = ASRMock(bus)
    chunker = SubtitleChunker(bus)
    printer = SomePrinter(bus)
    translator = TranslationBatchChatGPT(bus)

    await asyncio.gather(asr.run(), printer.run())

if __name__ == '__main__':
    asyncio.run(main())