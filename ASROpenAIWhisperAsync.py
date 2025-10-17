from openai import OpenAI


class ASROopenAIWhisperAsync:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.openAIClient = OpenAI()

    def getTranscript(self, audioFile, prompt, language):
        return self.openAIClient.audio.transcriptions.create(
            file=audioFile,
            language=language,
            model="whisper-1",
            prompt=prompt,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )