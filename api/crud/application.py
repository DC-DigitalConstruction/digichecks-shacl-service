from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Application
from api.schemas import ApplicatitonInDBSchema


async def db_get_application(db: AsyncSession, client_id: str):
    statement = select(Application).where(Application.client_id == client_id)
    result = await db.execute(statement)
    app = result.scalars().one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client_id or client_secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return app


async def db_create_application(
        db: AsyncSession, application: ApplicatitonInDBSchema):
    db_application = Application(
        client_id=str(application.client_id),
        hashed_client_secret=application.hashed_client_secret,
        role=application.role,
        company_id=application.company_id
    )

    db.add(db_application)
    await db.commit()
    await db.refresh(db_application)

    return db_application
