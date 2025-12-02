import pickle

from Config import fromLangCode, inputFile, outputFile, configWhisperPrompt, configTranslationContext, chatGPTModel
from TranslationBatchChatGPT import TranslationBatchChatGPT
from ASRFromSrtFile import ASRFromSrtFile
from ASROpenAIWhisper import ASROpenAIWhisper
from SubtitleWriter import writeSubtitles
from TranslationPassthrough import TranslationPassthrough
from Logger import logger

if __name__ == '__main__':
    ### speech to text
    # save transcript to file so we don't have to waste credits re-transcribing it in the future
    phrases = ASROpenAIWhisper().speechToText(inputFile, configWhisperPrompt, fromLangCode)
    with open(f"{outputFile}.pkl", "wb") as f:
        pickle.dump(phrases, f)
        f.close()

    # with open(f"{outputFile}.pkl", "rb") as f:
    #     phrases = pickle.load(f)

    # phrases = ASRFromSrtFile().speechToText(outputFile + ".srt")

    ### text to text translation
    TranslationBatchChatGPT().translate(phrases, configTranslationContext, chatGPTModel)
    # TranslationLocalGPTOSS().translate(phrases, configTranslationContext, "")
    # TranslationPassthrough().translate(phrases)

    ### write output to srt
    writeSubtitles(phrases, outputFile)
