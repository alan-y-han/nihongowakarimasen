from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel

from TranslationInterface import TranslationInterface
from logger import logger


marker = "newSubtitleLine"

def generatePrompt(extraPrompts, phrases, previousContext):
    # add instructions
    instructions = (
            "You are an expert Japanese to English translator. "
            # "Please translate the following srt subtitle file. "
            "Please translate the following lines from a subtitle file. "
            f"The beginning of each line is marked with [{marker} n] where n is the line number. "
            # "This marker should not be translated or modified in any way, and should be preserved as-is in the translated text. "
            "This marker should not be translated or included in the final translation for each line. "
            "Do not summarise or produce any extra text aside from the translation. "
            "Do not add, delete or merge any subtitle lines. "
            # "Only return the translated srt file - do not return any other extra text. "
            "The subtitles come from a machine generated transcription, and each subtitle line may be a whole sentence or a section of a sentence. "
            "There may be some inaccuracies in the Japanese text. "
            "If the sentence doesn't make sense, it is possible that some words were transcribed incorrectly, so consider if other similar sounding words make sense. "
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
    untranslatedSubList = []
    for i, phrase in enumerate(phrases, start=1):
        untranslatedSubList.append(f"[{marker} {i}] {phrase.text}")
    untranslatedSubs = "\n".join(untranslatedSubList)

    toTranslate = f"The subtitle lines to translate are as follows:\n\n{untranslatedSubs}"
    output.append(toTranslate)

    return "\n\n".join(output)


class TranslationOneShotChatGPT(TranslationInterface):

    def __init__(self):
        self.client = OpenAI(
            timeout=900.0
        )

    def translate(self, phrases, extraPrompts="", model="gpt-5") -> None:
        logger.info(f"Beginning ChatGPT oneshot translation. Number of lines to be translated: {len(phrases)}")

        class SubtitleLineTranslated(BaseModel):
            lineNumber: int
            translatedText: str

        class SubtitleFileTranslated(BaseModel):
            subtitleLines: list[SubtitleLineTranslated]

        chunkSize = 200
        splitPhrases = [phrases[i:i + chunkSize] for i in range(0, len(phrases), chunkSize)]
        previousContext = None

        for phraseChunk in splitPhrases:
            translationPrompt = generatePrompt(extraPrompts, phraseChunk, previousContext)
            translationStartTime = datetime.now()
            logger.info("Beginning section translation")
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
                # service_tier="flex",
                text_format=SubtitleFileTranslated
            )

            translatedOutputLines = response.output_parsed.subtitleLines
            translationTime = datetime.now() - translationStartTime
            subs = "\n".join([f"[{line.lineNumber:03d}] {line.translatedText}" for line in translatedOutputLines])
            logger.info(f"Received translation, time taken: {translationTime}")
            logger.info(f"Translated text:\n{subs}")
            logger.info(f"Token usage:\n{response.usage.model_dump_json(indent=2)}")

            # TODO: handle these errors
            if len(translatedOutputLines) != len(phraseChunk):
                raise Exception("Translation failed, total line count mismatch. "
                                f"Input was {len(phraseChunk)} lines but output was {len(translatedOutputLines)} lines")

            for i, (phrase, subtitleLine) in enumerate(zip(phraseChunk, translatedOutputLines), 1):
                if i != subtitleLine.lineNumber:
                    raise Exception("Translation failed, line number mismatch. "
                                    f"Input line number is {len(phraseChunk)} but output line number is {len(translatedOutputLines)}")
                phrase.translatedText = subtitleLine.translatedText

            previousContext = (
                    "\n".join([phrase.text for phrase in phraseChunk[-4:]])
                    + "\n\n"
                    + "\n".join([line.translatedText for line in translatedOutputLines[-4:]])
            )