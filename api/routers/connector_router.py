from fastapi import APIRouter, Depends, status, Security
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.app.connector import ConnectorInSchema, ConnectorOutSchema, ConnectorUpdateSchema
from api.dependencies.security import company_user_level
from api.dependencies.database import get_db
from api.crud.connector import (
    db_create_connector,
    db_get_connector,
    db_update_connector,
    db_delete_connector,
    db_get_all_connectors
)
from api.crud.companies import db_get_company


connector_router = APIRouter()


@connector_router.post(
    name='Create new API Connector',
    path='',
    status_code=status.HTTP_201_CREATED,
    response_model=ConnectorOutSchema,
    dependencies=[Security(company_user_level)]
)
async def create_connector(
    company_uuid: str,
    connector: ConnectorInSchema,
    db: AsyncSession=Depends(get_db)
):   
    db_company = await db_get_company(db, company_uuid)
    db_connector = await db_create_connector(db, connector, db_company.id)

    return db_connector


@connector_router.get(
    name='Get all connectors',
    path='/all',
    status_code=status.HTTP_200_OK,
    response_model=list[ConnectorOutSchema],
    dependencies=[Security(company_user_level)]
)
async def get_checks(
    company_uuid: str,
    db: AsyncSession=Depends(get_db)
):
    db_company = await db_get_company(db, company_uuid)
    db_checks = await db_get_all_connectors(db, db_company.id)
    return db_checks


@connector_router.get(
    name='Get an existing API Connector',
    path='/{connector_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=ConnectorOutSchema,
    dependencies=[Security(company_user_level)]
)
async def get_connectors(
    company_uuid: str,
    connector_uuid: str,
    db: AsyncSession=Depends(get_db)
):
    db_connector = await db_get_connector(db, connector_uuid)
    return db_connector


@connector_router.put(
    name='Update API Connector',
    path='/{connector_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=ConnectorOutSchema,
    dependencies=[Security(company_user_level)]
)
async def update_connector(
    company_uuid: str,
    connector_uuid: str,
    connector: ConnectorUpdateSchema,
    db: AsyncSession=Depends(get_db)
):
    db_connector = await db_get_connector(db, connector_uuid)
    db_connector = await db_update_connector(db, db_connector, connector)
    return db_connector


@connector_router.delete(
    name='Delete API Connector',
    path='/{connector_uuid}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(company_user_level)]
)
async def delete_connector(
    company_uuid: str,
    connector_uuid: str,
    db: AsyncSession=Depends(get_db)
):
    db_connector = await db_get_connector(db, connector_uuid)
    await db_delete_connector(db, db_connector)
    return None
