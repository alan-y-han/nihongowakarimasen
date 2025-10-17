import asyncio
from enum import Enum


class MessageType(str, Enum):
    ASR_FINAL = "ASR_FINAL"
    SUBTITLE_CHUNK = "SUBTITLE_CHUNK"


class MessageBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type):
        def decorator(callback):
            self.subscribers.setdefault(event_type, []).append(callback)
            return callback
        return decorator

    def publish(self, event_type, data):
        coroutines = [callback(data) for callback in self.subscribers.get(event_type, [])]
        for cr in coroutines:
            asyncio.create_task(cr)