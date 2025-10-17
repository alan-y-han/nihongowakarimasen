import pyaudio
from speechmatics.rt import AsyncClient, TranscriptionConfig, ServerMessageType, Microphone, OperatingPoint, \
    AudioFormat, AudioEncoding

from MessageBus import MessageBus, MessageType
from TranscribedPhrase import Word

# Japanese (ja) sounds_like only supports full width Hiragana or Katakana
# https://docs.speechmatics.com/speech-to-text/features/custom-dictionary
specialWords = [
        "クラリス", # ClariS
        "クララ", # Clara
        "エリイ", # Elly
        "アンナ", # Anna
        "うみつき", # Umitsuki
        "コネクト" # Connect
    ]

class ASRSpeechmatics:
    def __init__(self, messageBus: MessageBus):
        self.bus = messageBus

    async def run(self):
        p = pyaudio.PyAudio()

        deviceInfo = p.get_default_input_device_info()
        chunkSize = 1024
        deviceIndex = deviceInfo["index"]
        channels = 1
        sampleRate = int(deviceInfo["defaultSampleRate"])

        deviceName = deviceInfo["name"]
        print(f"Using <<{deviceName}>> which is deviceIndex {deviceIndex}")

        mic = Microphone(
            chunk_size=chunkSize,
            channels=channels,
            sample_rate=sampleRate,
            device_index=deviceIndex
        )

        async with AsyncClient() as client:
            # Register event handlers
            # @client.on(ServerMessageType.ADD_PARTIAL_TRANSCRIPT)
            # def handlePartialTranscript(msg):
            #     print(f"Partial: {msg['metadata']['transcript']}")

            @client.on(ServerMessageType.ADD_TRANSCRIPT)
            def handle_final_transcript(msg):
                # print(f"Final: {msg['metadata']['transcript']}")
                results = msg["results"]
                for result in results:
                    alternatives = result["alternatives"]
                    if not len(alternatives):
                        continue
                    # making assumption that results always come in chronological order
                    word = Word(
                        start=result["start_time"],
                        end=result["end_time"],
                        text=result["alternatives"][0]["content"]
                    )
                    self.bus.publish(MessageType.ASR_FINAL, word)

            transcriptionConf = TranscriptionConfig(
                language="ja",
                diarization="speaker",
                max_delay=1,
                # additional_vocab=[{word: word} for word in specialWords], # TODO: figure out why this crashes
                # enable_partials=True,
                operating_point=OperatingPoint.ENHANCED,  # default
                max_delay_mode="flexible"  # default
            )
            audioFormat = AudioFormat(
                encoding=AudioEncoding.PCM_S16LE,
                sample_rate=sampleRate,
                chunk_size=chunkSize
            )
            if mic.start():
                print("mic open")
                await client.transcribe(mic, transcription_config=transcriptionConf, audio_format=audioFormat)
            else:
                print("could not open mic")
            print("stopping mic")
            mic.stop()