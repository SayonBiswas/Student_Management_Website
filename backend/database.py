import databases
import sqlalchemy

from backend.config import settings

database = databases.Database(settings.DATABASE_URL)
metadata = sqlalchemy.MetaData()

async def connect_db():
    await database.connect()

async def disconnect_db():
    await database.disconnect()