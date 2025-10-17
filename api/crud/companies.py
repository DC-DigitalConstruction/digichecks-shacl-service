import datetime as dt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Company
from api.schemas import CompanyInSchema


async def db_get_company(db: AsyncSession, uuid: str):
    statement = select(Company).where(Company.uuid == uuid)
    result = await db.execute(statement)
    db_company = result.scalars().one_or_none()

    if db_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No company was found with that id.'
        )
    return db_company


async def db_create_company(db: AsyncSession, company: CompanyInSchema):
    db_company = Company(name=company.name, updated_at=dt.datetime.now())

    db.add(db_company)
    await db.commit()
    await db.refresh(db_company)

    return db_company


async def db_update_company(db: AsyncSession, db_company: Company, company_in: CompanyInSchema):
    for field, value in company_in.model_dump().items():
        if value:
            setattr(db_company, field, value)

    db_company.updated_at = dt.datetime.now()
    await db.commit()
    await db.refresh(db_company)
    return db_company


async def db_delete_company(db: AsyncSession, company: Company):
    await db.delete(company)
    await db.commit()
    return None


async def db_get_company_by_internal_id(db: AsyncSession, internal_id: int):
    statement = select(Company).where(Company.id == internal_id)
    result = await db.execute(statement)
    db_company = result.scalars().one()
    return db_company
