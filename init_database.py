import secrets
import uuid

from api.dependencies.database import async_session
from api.crud.application import db_create_application
from api.crud.companies import db_create_company
from api.schemas.core.application import ApplicatitonInDBSchema, ApplicationRole
from api.schemas.core.company import CompanyInSchema
from api.utils.hash import hash_password

async def create_super_user():
    db = async_session()

    # Create the company
    company = CompanyInSchema(name='Super User Company')
    db_company = await db_create_company(db, company)

    # Create the super user application
    client_id = str(uuid.uuid4())
    client_secret = secrets.token_urlsafe(24)
    super_user_application = ApplicatitonInDBSchema(
        company_id=db_company.id,
        client_id=client_id,
        hashed_client_secret=hash_password(client_secret),
        role=ApplicationRole.super_user
    )
    db_application = await db_create_application(db, super_user_application)

    print(f'Super user client_id: {client_id}')
    print(f'Super user client_secret: {client_secret}')

    await db.close()


if __name__ == '__main__':
    import asyncio

    asyncio.run(create_super_user())
