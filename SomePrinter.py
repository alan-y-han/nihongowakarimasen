import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

from rich.live import Live
from rich.panel import Panel

from AsyncUtils import serialSubscriber
from MessageBus import MessageType


@dataclass
class TranslatedLine:
    jpText: str
    uuid: str
    enTextDelta: str = ""
    enTextFinal: Optional[str] = None

class SomePrinter:
    def __init__(self, messageBus):
        self.bus = messageBus
        self.messageHistory = OrderedDict()
        self.maxHistorySize = 20
        self.latestJpTextDelta = ""
        self.renderEvent = asyncio.Event()
        serialSubscriber(self.bus, MessageType.ASR_FINAL)(self.onUntranslatedDelta)
        serialSubscriber(self.bus, MessageType.SUBTITLE_CHUNK)(self.onUntranslatedFinal)
        serialSubscriber(self.bus, MessageType.TRANSLATED_PHRASE_DELTA)(self.onTranslatedDelta)
        serialSubscriber(self.bus, MessageType.TRANSLATED_PHRASE_FINAL)(self.onTranslatedFinal)

    async def onUntranslatedDelta(self, data):
        self.latestJpTextDelta += data.text
        self.renderEvent.set()

    async def onUntranslatedFinal(self, data):
        newLine = TranslatedLine(jpText=data.text, uuid=data.uuid)
        self.messageHistory[data.uuid] = newLine
        if len(self.messageHistory) > self.maxHistorySize:
            self.messageHistory.popitem(last=False)
        self.renderEvent.set()
        self.latestJpTextDelta = ""

    async def onTranslatedDelta(self, data):
        if data.uuid in self.messageHistory:
            self.messageHistory[data.uuid].enTextDelta += data.text
        self.renderEvent.set()

    async def onTranslatedFinal(self, data):
        if data.uuid in self.messageHistory:
            self.messageHistory[data.uuid].enTextFinal = data.text
        self.renderEvent.set()

    def render(self):
        if self.latestJpTextDelta:
            maxLength = 9
        else:
            maxLength = 10

        output = []
        for uuid, msg in list(self.messageHistory.items())[-maxLength:]:
            output.append(msg.jpText)
            if msg.enTextFinal:
                output.append(msg.enTextFinal + "\n")
            else:
                output.append(msg.enTextDelta + "\n")
            # output.append(f"uuid: {msg.uuid}\njp: {msg.jpText}\nenDelta: {msg.enTextDelta}\nenFinal: {msg.enTextFinal}\n")

        if self.latestJpTextDelta:
            output.append(self.latestJpTextDelta)
            output.append("\n")

        return Panel("\n".join(output), title="Output", border_style="white")

    async def run(self):
        with Live(self.render(), refresh_per_second=10, screen=True) as live:
            while True:
                await self.renderEvent.wait()
                self.renderEvent.clear()
                live.update(self.render())