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

def batchedSerialSubscriber(bus, eventType):
    eventQueue = asyncio.Queue()

    def decorator(callback):
        @bus.subscribe(eventType)
        async def enqueue(data):
            await eventQueue.put(data)

        async def worker():
            while True:
                # 1. Block and wait for at least one item to arrive
                first_item = await eventQueue.get()
                batch = [first_item]

                # 2. Drain any other items that arrived while the worker was busy/waiting
                while not eventQueue.empty():
                    try:
                        # use get_nowait because we already know the queue isn't empty
                        batch.append(eventQueue.get_nowait())
                    except asyncio.QueueEmpty:
                        break

                # 3. Pass the entire batch to the callback
                try:
                    await callback(batch)
                except Exception as e:
                    # Handle exceptions so the worker loop doesn't crash permanently
                    print(f"Error processing batch: {e}")
                finally:
                    # 4. Acknowledge all processed items in the queue
                    for _ in range(len(batch)):
                        eventQueue.task_done()

        asyncio.create_task(worker())
        return callback

    return decorator