import uuid
from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel

from TranslationInterface import TranslationInterface
from logger import logger


def generatePrompt(extraPrompts, untranslatedSubs, previousContext):
    # add instructions
    instructions = (
            "You are an expert Japanese to English translator. "
            "You will be given lines from a subtitle file to translate. "
            "The beginning of each line is marked with [uuid] where uuid is a unique ID for that line. "
            "This marker should not be translated or included in the final translation. "
            "Do not add, remove or merge any subtitle lines. "
            "It is important that the uuid of the translated line matches the uuid of the original line. "
            "Do not summarise or produce any extra text aside from the translation. "
            "The subtitles come from a machine generated transcription. "
            "Each subtitle line may be a whole sentence or a section of a sentence. "
            "There may be some inaccuracies in the Japanese text. "
            "If the sentence doesn't make sense, it is possible that some words were transcribed incorrectly, "
            "so consider if other similar sounding words make sense. "
            + extraPrompts
    )
    output = [instructions]

    # add context from previous translation segment
    if previousContext:
        context = (
                "The preceding untranslated subtitle text and its translation are also provided here for context. "
                "Use this to help with your translation. "
                "Do not translate this part or include it in your response:\n\n"
                + previousContext
        )
        output.append(context)

    # finally add new subtitles to be translated
    toTranslate = f"The subtitle lines to translate are as follows:\n\n{untranslatedSubs}"
    output.append(toTranslate)

    return "\n\n".join(output)


def generateSubsToTranslate(phrases):
    toTranslateList = []
    uuidList = [uuid.uuid4().hex[:8] for _ in phrases]
    for lineID, phrase in zip(uuidList, phrases):
        toTranslateList.append(f"[{lineID}] {phrase.text}")
    subsToTranslate = "\n".join(toTranslateList)

    return uuidList, subsToTranslate


class TranslationOneShotChatGPT(TranslationInterface):

    def __init__(self):
        self.client = OpenAI(
            timeout=900.0
        )

    def translate(self, phrases, extraPrompts="", model="gpt-5") -> None:
        logger.info(f"Beginning ChatGPT oneshot translation. Number of lines to be translated: {len(phrases)}")

        class SubtitleLineTranslated(BaseModel):
            uuid: str
            translatedText: str

        class SubtitleFileTranslated(BaseModel):
            subtitleLines: list[SubtitleLineTranslated]

        chunkSize = 200
        splitPhrases = [phrases[i:i + chunkSize] for i in range(0, len(phrases), chunkSize)]
        previousContext = None

        for phraseChunk in splitPhrases:
            uuidList, toTranslate = generateSubsToTranslate(phraseChunk)
            translationPrompt = generatePrompt(extraPrompts, toTranslate, previousContext)

            translationStartTime = datetime.now()
            logger.info("--- Beginning section translation ---")
            logger.info(f"Translation prompt:\n{translationPrompt}")

            response = self.client.responses.parse(
                model=model,
                reasoning={
                    "effort": "low"
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

            translationTime = datetime.now() - translationStartTime
            subs = "\n".join([f"[{line.uuid}] {line.translatedText}" for line in translatedLines])
            logger.info(f"Received translation:\n{subs}")
            logger.info(f"Time taken: {translationTime}")
            logger.info(f"Token usage:\n{response.usage.model_dump_json(indent=2)}")

            # chatgpt doesn't always follow the prompt, so we must do error checking
            # TODO: handle these errors
            actualUuidList = [line.uuid for line in translatedLines]
            for i in range(len(uuidList)):
                if i >= len(uuidList):
                    raise Exception("Translation failed, received fewer lines than expected. "
                                    f"Input was {len(phraseChunk)} lines but output was {len(translatedLines)} lines. "
                                    f"Line [{uuidList[i]}] is missing")
                expectedUuid = uuidList[i]
                actualUuid = actualUuidList[i]
                if expectedUuid != actualUuid:
                    raise Exception("Translation failed, line UUID mismatch. "
                                    f"Input UUID is {expectedUuid} but output UUID is {actualUuid}")

            for i, (phrase, subtitleLine) in enumerate(zip(phraseChunk, translatedLines), 1):
                phrase.translatedText = subtitleLine.translatedText

            previousContext = (
                    "\n".join([phrase.text for phrase in phraseChunk[-4:]])
                    + "\n\n"
                    + "\n".join([line.translatedText for line in translatedLines[-4:]])
            )