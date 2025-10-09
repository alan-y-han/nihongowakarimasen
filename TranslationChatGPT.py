from collections import deque

from openai import OpenAI

from TranslationInterface import TranslationInterface


class TranslationChatGPT(TranslationInterface):
    def __init__(self):
        self.client = OpenAI()

    def translate(self, phrases, extraPrompts="", model="gpt-4.1"):
        instructions = (
            "You are an expert Japanese to English translator. "
            "Please translate any text given to you. "
            "Do not summarise or produce any extra text aside from the translation. "
            "You will receive sections of text from a machine generated transcription, which may be whole sentences or parts of a sentence. "
            "The surrounding text will also be provided as context to help you translate, but this should not be translated. "
            # "If the translation continues the previous sentence, don't capitalise the first word. "
            "There may be some inaccuracies in the Japanese text. "
            "If the sentence doesn't make sense, it is possible that some words were transcribed incorrectly, so consider if other similar sounding words make sense.") + extraPrompts
        initialPrompt = {
            "role": "developer",
            "content": f"{instructions}",
        }
        initialResponse = self.client.responses.create(
            model=model,
            input=[initialPrompt],
            store=False
        )

        def getOutput(response):
            return [{"role": el.role, "content": el.content} for el in response.output if el.type == "message"]

        historyPrefix = [initialPrompt] + getOutput(initialResponse)

        translationHistory = deque(maxlen=3)

        for i, phrase in enumerate(phrases):
            surroundingText = phrases[max(0, i - 2):min(len(phrases), i + 2)]
            content = (f"Please translate only this text to English: {phrase.text}"
                       f"\n\nThe surrounding text is also provided here for context only. Do not translate this part: "
                       f"{"".join([phrase.text for phrase in surroundingText])}")

            translationHistory.append({
                "role": "user",
                "content": f"{content}"
            })
            response = self.client.responses.create(
                model=model,
                # previous_response_id=prevResponse.id,
                input=historyPrefix + list(translationHistory),
                store=False
            )
            translationHistory += getOutput(response)

            phrase.translatedText = response.output_text
            print(f"> [{phrase.start:.1f} - {phrase.end:.1f}] {phrase.text}")
            print(phrase.translatedText)
            # print(historyPrefix + list(translationHistory))
            print("\n")