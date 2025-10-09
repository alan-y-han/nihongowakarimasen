import pickle

from TranslationOneShotChatGPT import TranslationOneShotChatGPT
from ASRFromSrtFile import ASRFromSrtFile
from ASROpenAIWhisper import ASROpenAIWhisper
from SubtitleWriter import writeSubtitles
from prompts import translationContextClarisSeason3, whisperPromptGeneric, translationContextClarisSeason2, \
    translationContextMizukiNana

folder = "C:/Users/pathtovideofolder/"
file = "filename"
fileExtension = ".mp4"

inputFile = folder + file + fileExtension
outputFile = folder + file


if __name__ == '__main__':
    ### speech to text
    phrases = ASROpenAIWhisper().speechToText(inputFile, whisperPromptGeneric, "ja")
    with open(f"{outputFile}.pkl", "wb") as f:
        pickle.dump(phrases, f)
        f.close()

    # with open(f"{outputFile}.pkl", "rb") as f:
    #     phrases = pickle.load(f)

    # phrases = ASRFromSrtFile().speechToText(outputFile + ".srt")

    ### text to text translation
    # TranslationChatGPT().translate(phrases, translationContext, "gpt-5")
    TranslationOneShotChatGPT().translate(phrases, translationContextClarisSeason3, "gpt-5")
    # TranslationPassthrough().translate(phrases)

    ### write output to srt
    writeSubtitles(phrases, outputFile)
