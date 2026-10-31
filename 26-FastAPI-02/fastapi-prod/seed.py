import asyncio, hashlib, os
from app.db import SessionLocal, UserRow, init_db


def scrypt(pw: str, salt: bytes) -> bytes:
    return hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)


async def seed():
    await init_db()
    users = [
        ("alice", os.getenv("ALICE_PASSWORD", "alice-secret-123"), "predict"),
        ("admin", os.getenv("ADMIN_PASSWORD", "admin-secret-123"), "predict admin"),
    ]
    async with SessionLocal() as session:
        for name, pw, scopes in users:
            salt = os.urandom(16)
            session.add(
                UserRow(
                    username=name,
                    salt=salt.hex(),
                    password_hash=scrypt(pw, salt).hex(),
                    scopes=scopes,
                )
            )
        await session.commit()
    print(f"seeded {len(users)} users")


if __name__ == "__main__":
    asyncio.run(seed())
