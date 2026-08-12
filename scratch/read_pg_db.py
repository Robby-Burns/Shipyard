import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import models
# We need to make sure python path includes project root
sys.path.append(".")
from app.database.models.intake import IntakeSession

async def main():
    # Database URL from docker-compose
    db_url = "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/shipyard"
    print("Connecting to:", db_url)
    try:
        engine = create_async_engine(db_url, echo=False)
        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_factory() as db:
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
    except Exception as e:
        print("Error connecting to PostgreSQL database:", e)

if __name__ == "__main__":
    asyncio.run(main())
