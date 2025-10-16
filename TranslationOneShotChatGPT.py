import uuid
from collections import deque
from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel

from Config import fromLang, toLang, chatGPTServiceTier, chatGPTReasoningEffort
from TranslationInterface import TranslationInterface
from Logger import logger


def generatePrompt(extraPrompts, untranslatedSubs, previousContext):
    # add instructions
    instructions = (
            f"You are an expert {fromLang} to {toLang} translator. "
            "You will be given lines from a subtitle file to translate. "
            f"For each line, translate it from {fromLang} to {toLang}. "
            # f"In the output, every {toLang} line must have a corresponding {fromLang} line. "
            "At the beginning of each line is a marker which looks like [uuid]. "
            "This marker must not be translated or included in the translation. "
            # "You must not add, remove or merge any lines. "
            # "The total number of output lines must be the same as the input. "
            # "The uuid of the translated line must match the uuid of the original line. "
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


def generatePreviousContextString(previousPhrases):
    if not len(previousPhrases):
        return ""

    return (
        "\n".join([phrase.text for phrase in previousPhrases])
        + "\n\n"
        + "\n".join([phrase.translatedText for phrase in previousPhrases])
    )


def checkValidTranslation(expectedUuidList, actualUuidList):
    # check number of lines in output matches input
    if len(expectedUuidList) != len(actualUuidList):
        logger.warn("Translation failed, different number of lines than expected. "
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

        # translating too many subtitles at once makes chatgpt more likely to not follow instructions
        chunkSize = 100
        splitPhrases = deque([phrases[i:i + chunkSize] for i in range(0, len(phrases), chunkSize)])
        previousPhrases = deque(maxlen=5)

        while len(splitPhrases):
            phraseChunk = splitPhrases.popleft()

            expectedUuidList, toTranslate = generateSubsToTranslate(phraseChunk)
            translationPrompt = generatePrompt(extraPrompts, toTranslate, generatePreviousContextString(previousPhrases))

            translationStartTime = datetime.now()
            logger.info(f"--- Beginning translation of {len(phraseChunk)} lines ---")
            logger.debug(f"Translation prompt:\n{translationPrompt}")

            response = self.client.responses.parse(
                model=model,
                reasoning={
                    "effort": chatGPTReasoningEffort
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
            logger.info("Received translation")
            logger.debug(f"Translation contents:\n{subs}")
            logger.info(f"Time taken: {translationTime}")
            logger.debug(f"Token usage:\n{response.usage.model_dump_json(indent=2)}")

            # chatgpt doesn't always follow the prompt, so we must do error checking
            # if errors are detected, we keep halving the number of subtitle lines
            # until we reach the base case of one line, which is virtually guaranteed to translate successfully
            actualUuidList = [line.uuid for line in translatedLines]
            if not checkValidTranslation(expectedUuidList, actualUuidList):
                if len(phraseChunk) <= 1:
                    logger.error(f"Could not translate {phraseChunk}")
                    for phrase in phraseChunk:
                        phrase.translatedText = "[translation error]"
                    continue

                pivot = len(phraseChunk) // 2
                phraseHalf1 = phraseChunk[:pivot]
                phraseHalf2 = phraseChunk[pivot:]
                splitPhrases.appendleft(phraseHalf2)
                splitPhrases.appendleft(phraseHalf1)

                logger.warn(f"Retrying translation with {pivot} lines")
                continue

            for i, (phrase, subtitleLine) in enumerate(zip(phraseChunk, translatedLines), 1):
                phrase.translatedText = subtitleLine.translatedText
                previousPhrases.append(phrase)
