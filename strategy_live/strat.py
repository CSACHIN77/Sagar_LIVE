import asyncio

async def worker(event: asyncio.Event):
    print("Worker: Waiting for the event to be set...")
    await event.wait()  # Wait until the event is set
    print("Worker: Event is set! Starting work...")
    # Simulate some work
    await asyncio.sleep(2)
    print("Worker: Work is done!")

async def controller(event: asyncio.Event):
    print("Controller: Preparing to set the event...")
    await asyncio.sleep(5)  # Simulate some delay before setting the event
    print("Controller: Setting the event now.")
    event.set()  # Set the event to allow the worker to proceed

async def main():
    event = asyncio.Event()
    
    # Start the worker and controller coroutines
    await asyncio.gather(worker(event), controller(event))

# Run the event loop
asyncio.run(main())
