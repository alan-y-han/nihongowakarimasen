from collections import deque

from openai import AsyncOpenAI
from openai.types.responses import ResponseCompletedEvent, ResponseTextDeltaEvent, ResponseOutputMessage

from AsyncUtils import serialSubscriber
from MessageBus import MessageType
from Prompts import translationContextClarisSeason3
from TranscribedPhrase import TranslatedPhrase


class TranslationSingleLineChatGPT:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.client = AsyncOpenAI(
            timeout=8 # TODO: maybe tune this
        )
        self.previousContext = deque(maxlen=5)
        serialSubscriber(self.bus, MessageType.SUBTITLE_CHUNK)(self.translate)
        # self.bus.subscribe(MessageType.SUBTITLE_CHUNK)(self.translate)

    async def translate(self, data):
        precedingSubtitlePrompt = ""
        if len(self.previousContext):
            precedingSubtitlePrompt = ("These are the preceding subtitles and their translations. They are provided for reference only and must **not** be translated:\n\n"
                                       f"{"\n".join([f"{jpText}" for jpText, enText in self.previousContext])}\n\n"
                                       f"{"\n".join([f"{enText}" for jpText, enText in self.previousContext])}\n\n")

        prompt = ("You are an expert translator specializing in Japanese to English subtitle translation.\n"
                  "The subtitles provided are **machine-transcribed**, so they may contain minor errors, typos, or inaccuracies.\n"
                  "Each subtitle line may be a **whole or partial sentence**, depending on how the subtitles were split. Translate each line faithfully while making it understandable in English.\n"
                  "Please correct these errors in your translation to produce fluent, natural English subtitles.\n\n"
                  "Use the following additional translation context for the script to inform translation decisions:\n"
                  f"- {translationContextClarisSeason3}\n\n"
                  f"{precedingSubtitlePrompt}"
                  "You must not output any text other than the English translation. "
                  "Now, translate the following subtitle line:\n"
                  f"{data.text}"
                  )

        enTextFinal = ""

        model = "gpt-5-mini"
        shouldStream = False
        if model == "gpt-5-nano":
            shouldStream = True

        def cleanText(s):
            return s.strip('\n\r').replace('\n', ' ').replace('\r', ' ')

        clientOutput = await self.client.responses.create(
            model=model,
            input=prompt,
            stream=shouldStream,
            reasoning={
                "effort": "minimal"
            },
        )

        if model == "gpt-5-nano":
            async for event in clientOutput:
                # if event.type == "response.output_text.delta":
                if isinstance(event, ResponseTextDeltaEvent):
                    enTextDelta = cleanText(event.delta)
                    # print(enTextFinal, end="", flush=True)
                    self.bus.publish(MessageType.TRANSLATED_PHRASE_DELTA, TranslatedPhrase(enTextDelta, data.uuid))
                if isinstance(event, ResponseCompletedEvent):
                    # print("\n\n", end="", flush=True)
                    for out in event.response.output:
                        if isinstance(out, ResponseOutputMessage) and len(out.content):
                            enTextFinal = cleanText(out.content[0].text)
                            # print(enTextFinal, end="")
                            break
        else:
            enTextFinal = cleanText(clientOutput.output_text)

        self.bus.publish(MessageType.TRANSLATED_PHRASE_FINAL, TranslatedPhrase(enTextFinal, data.uuid))
        context = (data.text, enTextFinal)
        self.previousContext.append (context)

# if __name__ == '__main__':
#     async def main():
#         bus = MessageBus()
#         foo = TranslationSingleLineChatGPT(bus)
#         await foo.translate(TranscribedPhrase(text="今回もたくさん質問を送っていただいて、どれにお答えしようか悩んじったよね。"))
#
#     asyncio.run(main())