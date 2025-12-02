import asyncio


def serialSubscriber(bus, eventType):
    eventQueue = asyncio.Queue()

    def decorator(callback):
        @bus.subscribe(eventType)
        async def enqueue(data):
            await eventQueue.put(data)

        async def worker():
            while True:
                item = await eventQueue.get()
                await callback(item)
                eventQueue.task_done()

        asyncio.create_task(worker())
        return callback

    return decorator