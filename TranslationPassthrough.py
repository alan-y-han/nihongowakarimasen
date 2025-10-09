from TranslationInterface import TranslationInterface


class TranslationPassthrough(TranslationInterface):
    def translate(self, phrases, extraPrompts = None, model = None):
        for phrase in phrases:
            phrase.translatedText = phrase.text