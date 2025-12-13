import asyncio
import weakref
import gc

class Handler:
    def __init__(self):
        self.value = 1

    async def do_work(self):
        self.value += 1
        print(f"Work done, value: {self.value}")

async def monitor_loop(handler_weak_ref, running_check):
    print("Loop started")
    while True:
        if not running_check():
            print("Running check failed")
            break
            
        handler = handler_weak_ref()
        if handler is None:
            print("Handler collected")
            break
        
        await handler.do_work()
        del handler
        
        await asyncio.sleep(0.1)
    print("Loop ended")

async def main():
    h = Handler()
    running = True
    
    task = asyncio.create_task(monitor_loop(weakref.ref(h), lambda: running))
    
    await asyncio.sleep(0.5)
    print("Simulating heavy GC...")
    gc.collect()
    await asyncio.sleep(0.5)
    
    print("Deleting handler...")
    del h
    gc.collect()
    
    await asyncio.sleep(0.5)
    running = False
    await task

if __name__ == "__main__":
    asyncio.run(main())