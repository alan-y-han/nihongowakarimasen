import uuid
from collections import deque
from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel

from Config import fromLang, toLang, chatGPTServiceTier
from TranslationInterface import TranslationInterface
from Logger import logger


def generatePrompt(extraPrompts, untranslatedSubs, previousContext):
    # add instructions
    instructions = (
            f"You are an expert {fromLang} to {toLang} translator. "
            "You will be given lines from a subtitle file to translate. "
            "The beginning of each line is marked with [uuid] where uuid is an ID for that line. "
            "This marker should not be translated or included in the final translation. "
            "Do not add, remove or merge any subtitle lines. "
            "It is important that the uuid of the translated line matches the uuid of the original line. "
            "Do not summarise or produce any extra text aside from the translation. "
            "The subtitles come from a machine generated transcription. "
            "Each subtitle line may be a whole sentence or a section of a sentence. "
            f"There may be some inaccuracies in the {fromLang} text. "
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

    # TODO: add next phrases to the end so it knows the following context
    # or simply chop off the end and re-translate it next loop

    return "\n\n".join(output)


'''
Generate a list of UUIDs for each subtitle line and concatenate it all into a
long string to send to ChatGPT for translation.
It seems UUIDs make ChatGPT less likely to merge or delete lines, vs using an
ordered numbered list.
'''
def generateSubsToTranslate(phrases):
    toTranslateList = []
    uuidList = [uuid.uuid4().hex[:4] for _ in phrases]
    for lineID, phrase in zip(uuidList, phrases):
        toTranslateList.append(f"[{lineID}] {phrase.text}")
    subsToTranslate = "\n".join(toTranslateList)

    return uuidList, subsToTranslate


def checkValidTranslation(expectedUuidList, actualUuidList):
    # check number of lines in output matches input
    if len(expectedUuidList) != len(actualUuidList):
        logger.warn("Translation failed, received fewer lines than expected. "
                    f"Input was {len(expectedUuidList)} lines but output was {len(actualUuidList)} lines. "
                    f"Missing line(s): {set(expectedUuidList) - set(actualUuidList)}. "
                    f"Extra line(s): {set(actualUuidList) - set(expectedUuidList)}")
        return False
    # check each line UUID matches the original and the ordering is the same
    for expectedUuid, actualUuid in zip(expectedUuidList, actualUuidList):
        if expectedUuid != actualUuid:
            logger.warn("Translation failed, line UUID mismatch. "
                        f"Input UUID is {expectedUuid} but output UUID is {actualUuid}")
            return False

    return True


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
        splitPhrases = deque([phrases[i:i + chunkSize] for i in range(0, len(phrases), chunkSize)])
        previousContext = None

        retryCount = 0
        maxRetries = 2

        while len(splitPhrases):
            phraseChunk = splitPhrases.popleft()

            expectedUuidList, toTranslate = generateSubsToTranslate(phraseChunk)
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
                service_tier=chatGPTServiceTier,
                text_format=SubtitleFileTranslated
            )
            translatedLines = response.output_parsed.subtitleLines

            translationTime = datetime.now() - translationStartTime
            subs = "\n".join([f"[{line.uuid}] {line.translatedText}" for line in translatedLines])
            logger.info(f"Received translation:\n{subs}")
            logger.info(f"Time taken: {translationTime}")
            logger.info(f"Token usage:\n{response.usage.model_dump_json(indent=2)}")

            # chatgpt doesn't always follow the prompt, so we must do error checking
            actualUuidList = [line.uuid for line in translatedLines]
            if not checkValidTranslation(expectedUuidList, actualUuidList):
                if retryCount >= maxRetries:
                    raise Exception("Ran out of retry attempts for translation, aborting")
                splitPhrases.appendleft(phraseChunk)
                retryCount += 1
                logger.warn(f"Retrying translation, attempt {retryCount} out of {maxRetries}")
                continue

            retryCount = 0

            for i, (phrase, subtitleLine) in enumerate(zip(phraseChunk, translatedLines), 1):
                phrase.translatedText = subtitleLine.translatedText

            previousContext = (
                    "\n".join([phrase.text for phrase in phraseChunk[-4:]])
                    + "\n\n"
                    + "\n".join([line.translatedText for line in translatedLines[-4:]])
            )