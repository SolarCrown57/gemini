import asyncio
import gc
import os
import psutil
import httpx
import ssl
from src.api.vertex_client import VertexAIClient
from unittest.mock import MagicMock, patch

def get_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

async def test_leak():
    print(f"Initial Memory: {get_memory_mb():.2f} MB")
    
    # Mock dependencies
    mock_cred_manager = MagicMock()
    mock_stats_manager = MagicMock()
    
    client = VertexAIClient(mock_cred_manager, mock_stats_manager)
    
    iterations = 500
    
    # Spy on ssl.create_default_context
    with patch('ssl.create_default_context', side_effect=ssl.create_default_context) as mock_ssl:
        # Warmup
        for _ in range(10):
            async with client._create_isolated_client() as c:
                pass
        
        print(f"SSL Context created {mock_ssl.call_count} times during warmup")
        mock_ssl.reset_mock()
        
        gc.collect()
        start_mem = get_memory_mb()
        print(f"Start Memory (after warmup): {start_mem:.2f} MB")
        
        for i in range(iterations):
            # Simulate what happens in stream_chat
            async with client._create_isolated_client() as c:
                # Force SSL context load if lazy?
                # accessing private members is risky but necessary to prove creation
                # However, just creating the client might not trigger it if lazy.
                # But creating it with verify=True (default) usually does validation of cert paths.
                pass 
                
            if i % 100 == 0:
                gc.collect()
                current = get_memory_mb()
                print(f"Iteration {i}: {current:.2f} MB (Diff: {current - start_mem:.2f} MB)")
                
        gc.collect()
        end_mem = get_memory_mb()
        diff = end_mem - start_mem
        
        print(f"Final Memory: {end_mem:.2f} MB")
        print(f"Difference: {diff:.2f} MB")
        print(f"SSL Context created {mock_ssl.call_count} times during test")

        if diff > 20: 
            print("FAIL: Memory leak detected")
        elif mock_ssl.call_count > 10:
             print("FAIL: High number of SSL Context creations detected")
        else:
            print("PASS: No significant memory leak and low SSL context churn")

if __name__ == "__main__":
    asyncio.run(test_leak())