import datetime as dt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Connector
from api.schemas.app.connector import ConnectorInSchema


async def db_get_connector(db: AsyncSession, uuid: str):
    statement = select(Connector).where(Connector.uuid == uuid)
    result = await db.execute(statement)
    db_connector = result.scalars().one_or_none()

    if db_connector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No connector was found with that id.'
        )
    return db_connector


async def db_get_connector_by_internal_id(db: AsyncSession, internal_id: int):
    statement = select(Connector).where(Connector.id == internal_id)
    result = await db.execute(statement)
    db_connector = result.scalars().one_or_none()

    if db_connector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No connector was found with that id.'
        )
    return db_connector

async def db_create_connector(db: AsyncSession, connector: ConnectorInSchema, company_id: int):
    # Add the connector to the database
    db_connector = Connector(
        connector_name=connector.connector_name,
        token_endpoint=connector.token_endpoint,
        username=connector.username,
        password=connector.password,
        company_id=company_id,
        updated_at=dt.datetime.now()
    )

    # Encrypt the password before adding it to the database
    db_connector.password = db_connector.encrypt_password()

    db.add(db_connector)
    await db.commit()
    await db.refresh(db_connector)

    return db_connector


async def db_update_connector(db: AsyncSession, db_connector: Connector, connector_in: ConnectorInSchema):
    for field, value in connector_in.model_dump().items():
        if value:
            if field == 'password':
                value = db_connector.encrypt_password()
            setattr(db_connector, field, value)

    db_connector.updated_at = dt.datetime.now()
    await db.commit()
    await db.refresh(db_connector)
    return db_connector


async def db_delete_connector(db: AsyncSession, connector: Connector):
    await db.delete(connector)
    await db.commit()
    return None


async def db_get_all_connectors(db: AsyncSession, company_id: int):
    statement = select(Connector).where(Connector.company_id == company_id)
    result = await db.execute(statement)
    db_connectors = result.scalars().all()
    return db_connectors
