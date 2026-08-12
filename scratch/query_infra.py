import asyncio
import jwt
import httpx
from datetime import datetime, timedelta, timezone
from app.config.settings import settings

async def query():
    # Create a valid token
    payload = {
        "sub": "test-user",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.get("http://localhost:8000/api/v1/infrastructure", headers=headers)
        print("Status Code:", res.status_code)
        print("Response:", res.json())

if __name__ == "__main__":
    asyncio.run(query())
