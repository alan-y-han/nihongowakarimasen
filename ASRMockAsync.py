import asyncio

from MessageBus import MessageType
from TranscribedPhrase import Word

class ASRMock:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.mockMessages = [
            "クラリスネット。",
            "内緒の話。",
            "クラリスのクララです。",
            "エリーです。",
            "アンナです。",
            "クラリスネット。",
            "内緒の話Vol97。",
            "今回はクラリス相談室をお送りします。",
            "質問をたくさん送ってくださった皆さんありがとうございました。",
            "今回もたくさん質問を送っていただいて、どれにお答えしようか悩んじったよね。",
            "できる限りたくさん答えていきたいと思うので。",
            "皆さん最後まで楽しんでください。",
            "それでは早速いきましょう。",
            "それでは一つ目の質問です。",
            "私は高校2年生です。",
            "大学の学部選びについてめちゃくちゃ悩んでいます。",
            "理系学部に進みたいなと思い、この夏いくつかの大学のオープンキャンパスにも行ったのですが。",
            "挑戦したい学問が多すぎて、絞り切れずに、ただ心の中にモヤモヤしたものだけが残ってしまいました。",
            "クラリスの皆さんは、もしこのようなことが起こった時。",
            "どのように対処しますかとのことです。"
        ]

    async def run(self):
        time = 0
        for msg in self.mockMessages:
            for c in msg:
                self.bus.publish(MessageType.ASR_FINAL, Word(start=time, end=time + 0.1, text=c))
                time += 0.1
                await asyncio.sleep(0.1)
            time += 2
            await asyncio.sleep(2)