import asyncio

from ASRSpeechmaticsAsync import ASRSpeechmatics
from MessageBus import MessageBus
from SomePrinter import SomePrinter
from SubtitleChunkerAsync import SubtitleChunker
from TranslationSingleLineChatGPTAsync import TranslationSingleLineChatGPT


async def main():
    bus = MessageBus()

    asr = ASRSpeechmatics(bus)
    chunker = SubtitleChunker(bus)
    # printer = SomePrinter(bus)
    translator = TranslationSingleLineChatGPT(bus)

    await asr.run()

if __name__ == '__main__':
    asyncio.run(main())