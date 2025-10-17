import asyncio

import openai
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent

from MessageBus import MessageType, MessageBus


class TranslationSingleLineChatGPT:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.client = AsyncOpenAI()
        self.previousContextJa = []
        self.previousContextEn = []
        self.bus.subscribe(MessageType.SUBTITLE_CHUNK)(self.translate)

    async def translate(self, data):
        prompt = (f"Translate this sentence to English:\n{data.text}\n\n"
                  "Do not output any other text except the translation. ")
        if self.previousContextJa:
            prompt += f"To help you translate, the previous line was {self.previousContextJa}"

        stream = await self.client.responses.create(
            model="gpt-5-nano",
            input=prompt,
            stream=True,
            reasoning={
                "effort": "minimal"
            },
        )

        async for event in stream:
            if isinstance(event, ResponseTextDeltaEvent):
                print(event.delta, end="")
            # else:
                # print(f"received {type(event).__name__}")
        print("\n")

        self.previousContextJa = data.text
