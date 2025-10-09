import pycountry
from openai.types import ResponsesModel

from Types import ServiceTier
from Prompts import translationContextClarisSeason3, whisperPromptGenericJA, translationContextClarisSeason2, \
    translationContextMizukiNana, translationContextBlueArchive, whisperPromptGenericKO

# These arguments will get moved to a proper CLI interface in the future

fromLang = "Japanese"
fromLangCode = pycountry.languages.get(name=fromLang).alpha_2
toLang = "English"
toLangCode = pycountry.languages.get(name=toLang).alpha_2

folder = "C:/Users/pathToFolder/"
file = "videoFile"
fileExtension = ".mp4"

inputFile = folder + file + fileExtension
outputFile = folder + file

configWhisperPrompt = whisperPromptGenericJA
configTranslationContext = translationContextClarisSeason3

chatGPTServiceTier:ServiceTier = "default" # set to "flex" to save cost
chatGPTModel:ResponsesModel = "gpt-5"
chatGPTReasoningEffort = "low"
