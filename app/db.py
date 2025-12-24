# ORM = Object Relational Mapping

#Object-Relational Mapping (ORM) converts database tables
#into Python classes/objects, letting you work with data using
#object-oriented code instead of raw SQL queries.

# Allows you to prevent sql-code / nosql queries but to write python like code
#to define, retrie, create data

#sqlalchemy is one example

from collections.abc import AsyncGenerator
import uuid
from datetime import datetime

from fastapi import Depends
from fastapi_users import models
from sqlalchemy import Column,String,Text,DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import registry,relationship,sessionmaker
from datetime import datetime
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTable, SQLAlchemyBaseUserTableUUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.session import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

# Data models

mapper_registry = registry()
Base = mapper_registry.generate_base()

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    posts = relationship("Post",back_populates="user",lazy='selectin')#Creating a relationship between posts and user


######## For post #####

class Post(Base):
    __tablename__ = "posts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"),nullable=False)
    title = Column(String)
    caption = Column(Text)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User",back_populates="posts")


#This will create the database as well as the tables
async def create_db_and_tables():
    async with engine.begin() as conn:
        #Find all classes that inherit from the Declarative base and create them into the database
        await conn.run_sync(Base.metadata.create_all)

#It gets a session that allows us to actually access the database and write and read from it asynchronously
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


## fUNCTION TO GET THE USER DATABASE TABLE
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

