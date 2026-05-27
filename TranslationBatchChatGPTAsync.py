import asyncio
from collections import deque

from openai import AsyncOpenAI
from openai.types.responses import ResponseCompletedEvent, ResponseTextDeltaEvent, ResponseOutputMessage
from pydantic import BaseModel

from AsyncUtils import batchedSerialSubscriber
from Config import chatGPTReasoningEffort, chatGPTServiceTier
from MessageBus import MessageType
from Prompts import translationContextClarisSeason3
from TranscribedPhrase import TranslatedPhrase, TranscribedPhrase
from TranslationBatchChatGPT import generatePrompt, checkValidTranslation


class TranslationBatchChatGPT:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.client = AsyncOpenAI(
            timeout=8 # TODO: maybe tune this
        )
        self.previousPhrases = deque(maxlen=5)
        batchedSerialSubscriber(self.bus, MessageType.SUBTITLE_CHUNK)(self.translate)

    async def translate(self, subtitleChunk):
        extraPrompts = ""
        model = "gpt-5.4-mini"

        class SubtitleLineTranslated(BaseModel):
            id: str
            en: str

        class SubtitleFileTranslated(BaseModel):
            subtitleLines: list[SubtitleLineTranslated]

        translationPrompt = generatePrompt(extraPrompts, subtitleChunk, self.previousPhrases)

        response = await self.client.responses.parse(
                model=model,
                reasoning={
                    "effort": chatGPTReasoningEffort
                },
                input=[{
                    "role": "user",
                    "content": translationPrompt
                }],
                store=False,
                service_tier="flex",
                text_format=SubtitleFileTranslated
            )
        translatedLines = response.output_parsed.subtitleLines

        # TODO: do basic checking
        # if

        foo = list(zip(translatedLines, subtitleChunk))

        for subtitleLine, subtitleChunkObj in foo:
            enTextFinal = subtitleLine.en
            self.bus.publish(MessageType.TRANSLATED_PHRASE_FINAL, TranslatedPhrase(enTextFinal, subtitleChunkObj.uuid))
            context = TranscribedPhrase(text=subtitleChunkObj.text, translatedText=enTextFinal)
            self.previousPhrases.append (context)
