import gc

import torch
import whisperx

from TranscribedPhrase import TranscribedPhrase
from ASRInterface import ASRInterface


class ASRLocalWhisper(ASRInterface):
    def speechToText(self, filepath, prompt, language):
        resultAligned = doASR(filepath, prompt, language)
        return getChunks(resultAligned)

def doASR(pathToFile, prompt, language):
    customAsrOptions = {
        # "beam_size": 5,
        # "best_of": 5,
        # "patience": 1,
        # "length_penalty": 1,
        # "repetition_penalty": 1,
        # "no_repeat_ngram_size": 0,
        # "temperatures": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        # "compression_ratio_threshold": 2.4,
        # "log_prob_threshold": -1.0,
        # "no_speech_threshold": 0.6,
        # "condition_on_previous_text": False,
        # "prompt_reset_on_temperature": 0.5,
        "initial_prompt": "これはトークショーです。",
        # "prefix": None,
        # "suppress_blank": True,
        # "suppress_tokens": [-1],
        # "without_timestamps": True,
        # "max_initial_timestamp": 0.0,
        # "word_timestamps": False,
        # "prepend_punctuations": "\"'“¿([{-",
        # "append_punctuations": "\"'.。,，!！?？:：”)]}、",
        # "multilingual": model.model.is_multilingual,
        # "suppress_numerals": False,
        # "max_new_tokens": None,
        # "clip_timestamps": None,
        # "hallucination_silence_threshold": None,
        # "hotwords": None,
    }

    customAsrOptions.update({"initial_prompt": prompt})

    model = whisperx.load_model(
        "large-v2",
        "cuda",
        language=language,
        compute_type="float16",
        download_root="/models/",
        asr_options=customAsrOptions
    )
    audio = whisperx.load_audio(pathToFile)
    result = model.transcribe(audio, batch_size=16, language=language)

    print("--- raw transcript ---")
    jpText = [seg["text"] for seg in result["segments"]]
    print(jpText)

    # align whisper output
    modelAligned, metadata = whisperx.load_align_model(
        language_code=result["language"],
        device="cuda",
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-japanese"
    )
    resultAligned = whisperx.align(result["segments"], modelAligned, metadata, audio, "cuda",
                                   return_char_alignments=False)
    cleanUpGPU([model, modelAligned])
    return resultAligned

def cleanUpGPU(modelsToDelete):
    gc.collect()
    torch.cuda.empty_cache()
    for model in modelsToDelete:
        del model

def getChunks(resultAligned):
    toBreakOn = {"。", "？", "?"} #"、", ",", ".",
    chunks = []
    currentPart = None

    for segment in resultAligned["segments"]:
        for word in segment["words"]:
            if not currentPart:
                currentPart = TranscribedPhrase()
            currentPart.text += word["word"]
            if currentPart.start is None and "start" in word:
                currentPart.start = word["start"]
            if "end" in word:
                currentPart.end = word["end"]

            if word["word"] in toBreakOn:
                chunks.append(currentPart)
                currentPart = None
        # include the current sentence even if it hasn't ended
        if currentPart:
            chunks.append(currentPart)
            currentPart = None
    # include the current sentence even if it hasn't ended
    if currentPart:
        chunks.append(currentPart)

    return chunks
