import json

class MockRequest:
    def __init__(self, url, post_data):
        self.url = url
        self.post_data = post_data
        self.headers = {}

    async def all_headers(self):
        return self.headers

class Harvester:
    TARGET_PATTERNS = [
        "batchGraphql",
        "StreamGenerateContent"
    ]
    
    def is_target_request(self, url: str) -> bool:
        return any(pattern in url for pattern in self.TARGET_PATTERNS)

    async def handle_request(self, request):
        url = request.url
        post_data_str = request.post_data
        
        if not self.is_target_request(url):
            print(f"Ignored by URL: {url}")
            return False

        CONTENT_KEYWORDS = ['StreamGenerateContent', 'generateContent', 'Predict', 'Image']
        is_content_request = any(kw in post_data_str for kw in CONTENT_KEYWORDS)
        
        if not is_content_request:
            print(f"Ignored by Body Check. URL: {url}, Body: {post_data_str}")
            return False
            
        print(f"Captured! URL: {url}")
        return True

async def test():
    h = Harvester()
    
    # Case 1: BatchGraphql with generateContent (Should pass)
    print("--- Case 1 ---")
    req1 = MockRequest(
        "https://console.cloud.google.com/m/batchGraphql",
        '[{"id":"generateContent","data":{...}}]'
    )
    await h.handle_request(req1)
    
    # Case 2: StreamGenerateContent REST style (Might fail if keyword not in body)
    print("\n--- Case 2 ---")
    req2 = MockRequest(
        "https://console.cloud.google.com/v1/projects/.../locations/.../publishers/google/models/gemini-pro:streamGenerateContent?alt=sse",
        '{"contents": [{"role": "user", "parts": [{"text": "hi"}]}], "generationConfig": {...}}'
    )
    await h.handle_request(req2)
    
    # Case 3: StreamGenerateContent with keyword in body (Should pass)
    print("\n--- Case 3 ---")
    req3 = MockRequest(
        "https://console.cloud.google.com/.../streamGenerateContent",
        '{"contents": ... "something": "StreamGenerateContent"}' 
    )
    await h.handle_request(req3)

import asyncio
asyncio.run(test())