import textwrap
from collections import deque
from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel

from Config import fromLang, toLang, chatGPTServiceTier, chatGPTReasoningEffort
from TranslationInterface import TranslationInterface
from Logger import logger


def generatePrompt(extraPrompts, untranslatedSubs, previousContext):
    instructions = textwrap.dedent(
        f"""\
        You are a precise translator specializing in Japanese-to-English subtitle translation.
        
        Your task:
        Translate the TARGET lines into English while using the MEMORY block for narrative continuity,
        character consistency, tone, naming conventions, and handling ambiguous references.
        
        MEMORY (context block):
        - The MEMORY block may contain zero or more previously translated subtitle pairs.
        - If MEMORY is empty, treat the translation as the beginning of the scene and do NOT assume any prior context.
        - When MEMORY is present, each item includes:
            - "id": numeric line ID
            - "ja": the original Japanese subtitle line
            - "en": the previously translated English line
        - MEMORY lines are NOT to be translated again.
        - NEVER output, modify, or repeat MEMORY lines.
        - MEMORY exists ONLY as contextual reference to maintain style, pronouns, tone, speaking manner,
          and naming consistency.
        - You may use MEMORY to infer consistent translation choices, but NEVER hallucinate details not
          present in either MEMORY or TARGET.
        
        TARGET (lines to translate):
        - Translate ONLY the lines inside the TARGET block.
        - If the Japanese text is slightly wrong but clearly intended to be something recognizable, correct it silently and translate the intended meaning.
        - Keep strict 1:1 alignment with IDs between target lines and their translations.
        - Do NOT merge, split, omit, or add lines.
        - Do NOT summarize.
        - Preserve tone, emotion, and speaker intent.
        - Output ONLY the structured JSON specified by the API (no explanations).
        
        General style rules:
        - Use clear, natural English suitable for timed subtitles.
        - Resolve pronouns consistently with MEMORY.
        - If ambiguity exists even with MEMORY, choose a neutral faithful translation.
        - Use English punctuation conventions.
        
        """)

    additionalContext = textwrap.dedent(
f"""
Additional translation context:
{extraPrompts}
""")

    example = textwrap.dedent(
        """\
        Example:
        
        MEMORY:
        [
          { "id": 11, "ja": "本気でそんなことを言ってるの？", "en": "Do you seriously mean that?" },
          { "id": 12, "ja": "嘘だと言ってよ。", "en": "Tell me it's a lie." }
        ]
        
        TARGET:
        {
          "subtitle_lines": [
            { "id": 13, "ja": "信じたくない。" },
            { "id": 14, "ja": "でも前に進まなきゃ。" }
          ]
        }
        
        Expected output (structure only):
        {
          "subtitle_lines_translated": [
            { "id": 13, "en": "I don't want to believe it." },
            { "id": 14, "en": "But I have to keep moving forward." }
          ]
        }
        
        If id 14 was missing for example, this would be an incorrect output because a line from TARGET is missing.
        You MUST ensure there are no missing lines.
        
        ---
        
        """)
    memory = []
    for i, phrase in enumerate(previousContext, start=1):
        indent = "  "
        line = f'\n{indent}{{ "id": {i}, "ja": "{phrase.text}", "en": "{phrase.translatedText}" }}'
        memory.append(line)

    jaLines = []
    for i, phrase in enumerate(untranslatedSubs, start=len(memory) + 1):
        indent = "    "
        line = f'\n{indent}{{ "id": {i}, "ja": "{phrase.text}" }}'
        jaLines.append(line)

    data = textwrap.dedent(f"""\
Now translate the following:
MEMORY:
[{",".join(memory)}
]

TARGET:
{{
  "subtitle_lines": [{",".join(jaLines)}
  ]
}}
)""")

    # TODO: add next phrases to the end so it knows the following context
    # or simply chop off the end and re-translate it next loop

    return instructions + additionalContext + example + data


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
            id: str
            en: str

        class SubtitleFileTranslated(BaseModel):
            subtitleLines: list[SubtitleLineTranslated]

        # translating too many subtitles at once makes chatgpt more likely to not follow instructions
        chunkSize = 200
        splitPhrases = deque([phrases[i:i + chunkSize] for i in range(0, len(phrases), chunkSize)])
        previousPhrases = deque(maxlen=5)

        while len(splitPhrases):
            phraseChunk = splitPhrases.popleft()

            translationPrompt = generatePrompt(extraPrompts, phraseChunk, previousPhrases)

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
            subs = "\n".join([f"[{line.id}] {line.en}" for line in translatedLines])
            logger.info("Received translation")
            logger.debug(f"Translation contents:\n{subs}")
            logger.info(f"Time taken: {translationTime}")
            logger.debug(f"Token usage:\n{response.usage.model_dump_json(indent=2)}")

            # chatgpt doesn't always follow the prompt, so we must do error checking
            # if errors are detected, we keep halving the number of subtitle lines
            # until we reach the base case of one line, which is virtually guaranteed to translate successfully
            actualUuidList = [line.id for line in translatedLines]
            if not checkValidTranslation([str(n) for n in range(len(previousPhrases) + 1, len(previousPhrases) + len(phraseChunk) + 1)], actualUuidList):
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
                phrase.translatedText = subtitleLine.en
                previousPhrases.append(phrase)
