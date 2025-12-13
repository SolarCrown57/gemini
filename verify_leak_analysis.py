import asyncio
import gc
import weakref
from src.headless.terms_handler import TermsHandler

class MockPage:
    async def evaluate(self, script):
        pass

async def test_terms_handler_cycle():
    print("Testing TermsHandler circular reference...")
    
    mock_page = MockPage()
    handler = TermsHandler(page=mock_page)
    handler_ref = weakref.ref(handler)
    
    # 模拟运行检查
    def is_running():
        return True
        
    # 启动监控
    await handler.start_monitoring(is_running_check=is_running)
    
    print(f"Monitoring started. Task exists: {handler._monitor_task is not None}")
    
    # 移除强引用
    del handler
    gc.collect()
    
    if handler_ref() is None:
        print("PASS: Handler was garbage collected immediately (unexpected if cycle exists)")
    else:
        print("FAIL: Handler was NOT garbage collected (cycle confirmed)")
        
        # 现在尝试清理
        handler = handler_ref()
        if handler:
            await handler.stop_monitoring()
            del handler
            gc.collect()
            if handler_ref() is None:
                print("PASS: Handler collected after stop_monitoring()")
            else:
                print("FAIL: Handler still alive after stop_monitoring()")

async def main():
    await test_terms_handler_cycle()

if __name__ == "__main__":
    asyncio.run(main())