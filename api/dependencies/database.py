from dataclasses import dataclass
import uuid

from sqlalchemy import event, String, Column, DateTime, Integer, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker, 
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase, mapper

from api.dependencies.config import settings


engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()


class BaseModel(DeclarativeBase):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, unique=True)
    uuid = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_onupdate=func.now())

    @staticmethod
    def generate_uuid(prefix: str)->str:
        return prefix + '_' + str(uuid.uuid4()).replace('-', '')


@event.listens_for(mapper, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.uuid = target.generate_uuid(
        target.__id_prefix__)


@dataclass
class Table:
    schema_name: str
    table_name: str

    def __str__(self)->str:
        return f'{self.schema_name}.{self.table_name}'

    @property
    def identifier(self)->str:
        return f'{self.schema_name}.{self.table_name}.id'


CORE_SCHEMA = 'core'
APP_SCHEMA = 'compliance'

APPLICATION_TABLE = Table(CORE_SCHEMA, 'applications')
COMPANY_TABLE = Table(CORE_SCHEMA, 'companies')
CHECK_TABLE = Table(APP_SCHEMA, 'checks')
CONNECTOR_TABLE = Table(APP_SCHEMA, 'connectors')