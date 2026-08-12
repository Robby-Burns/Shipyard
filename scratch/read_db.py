import asyncio
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.database.models.intake import IntakeSession

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(IntakeSession).order_by(IntakeSession.created_at.desc()))
        sessions = result.scalars().all()
        if not sessions:
            print("No sessions found in PostgreSQL!")
            return
        
        for session in sessions:
            print("=" * 60)
            print("SESSION ID:", session.id)
            print("TITLE:", session.title)
            print("STATUS:", session.status)
            print("SPECIFICATION LENGTH:", len(session.specification) if session.specification else 0)
            print("\n--- MESSAGES ---")
            for msg in session.messages:
                print(f"[{msg['role'].upper()}]:")
                content = msg['content']
                if len(content) > 300:
                    print(content[:300] + "... (TRUNCATED)")
                else:
                    print(content)
                print("-" * 40)
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
