import asyncio
import httpx

async def fetch():
    async with httpx.AsyncClient() as client:
        res = await client.get("http://[::1]:8000/debug-env")
        print("Status:", res.status_code)
        import json
        print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(fetch())
