from fastapi import APIRouter, Depends, status, Security
from sqlalchemy.ext.asyncio import AsyncSession

from api.crud.companies import (
    db_create_company,
    db_get_company,
    db_update_company,
    db_delete_company
)
from api.dependencies import (
    get_db,
    super_user_level,
    company_admin_level, 
    company_user_level
)
from api.schemas import CompanyInSchema, CompanyOutSchema


router = APIRouter()


@router.get(
    name='Get Company',
    path='/{company_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=CompanyOutSchema,
    dependencies=[Security(company_user_level)]
)
async def get_company(
    company_uuid: str,
    db: AsyncSession = Depends(get_db)
):
    db_company = await db_get_company(db, company_uuid)
    return db_company


@router.post(
    name='Create Company',
    path='',
    status_code=status.HTTP_201_CREATED,
    response_model=CompanyOutSchema,
    dependencies=[Security(super_user_level)]
)
async def create_company(
    company: CompanyInSchema,
    db: AsyncSession = Depends(get_db)
):
    db_company = await db_create_company(db, company)
    return db_company

@router.put(
    name='Update Company',
    path='/{company_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=CompanyOutSchema,
    dependencies=[Security(company_admin_level)]
)
async def update_company(
    company_uuid: str,
    company: CompanyInSchema,
    db: AsyncSession = Depends(get_db)
):
    db_company = await db_get_company(db, company_uuid)
    db_company = await db_update_company(db, db_company, company)
    return db_company


@router.delete(
    name='Delete Company',
    path='/{company_uuid}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(super_user_level)]
)
async def delete_company(
    company_uuid: str,
    db: AsyncSession = Depends(get_db)
):
    db_company = await db_get_company(db, company_uuid)
    db_company = await db_delete_company(db, db_company)
    return None
