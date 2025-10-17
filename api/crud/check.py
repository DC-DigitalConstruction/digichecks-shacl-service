import datetime as dt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Check
from api.schemas.app.check import CheckInSchema


async def db_get_check(db: AsyncSession, uuid: str):
    statement = select(Check).where(Check.uuid == uuid)
    result = await db.execute(statement)
    db_check = result.scalars().one_or_none()

    if db_check is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No check was found with that id.'
        )
    return db_check


async def db_create_check(
        db: AsyncSession, check: CheckInSchema, company_id: int, connector_id: int=None):
    db_check = Check(
        check_name=check.check_name,
        rule_source=check.rule_source,
        rule=check.rule,
        company_id=company_id,
        connector_id=connector_id if connector_id else None,
        updated_at=dt.datetime.now()
    )

    db.add(db_check)
    await db.commit()
    await db.refresh(db_check)

    return db_check


async def db_update_check(db: AsyncSession, db_check: Check, check_in: CheckInSchema):
    for field, value in check_in.model_dump().items():
        if value:
            setattr(db_check, field, value)

    db_check.updated_at = dt.datetime.now()
    await db.commit()
    await db.refresh(db_check)
    return db_check


async def db_delete_check(db: AsyncSession, check: Check):
    await db.delete(check)
    await db.commit()
    return None


async def db_get_all_checks(db: AsyncSession, company_id: int):
    statement = select(Check).where(Check.company_id == company_id)
    result = await db.execute(statement)
    db_checks = result.scalars().all()
    return db_checks
