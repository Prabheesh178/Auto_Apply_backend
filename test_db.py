import asyncio
from app.database import engine, Base, AsyncSessionLocal
from app.utils.seed_data import initialize_seed_data

async def test():
    print("Testing DB table creation...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    print("Testing seed data...")
    async with AsyncSessionLocal() as session:
        await initialize_seed_data(session)
    print("Seed data populated.")

    await engine.dispose()
    print("All backend DB tests PASSED!")

if __name__ == "__main__":
    asyncio.run(test())
