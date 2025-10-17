from datetime import datetime, timedelta
from typing import Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from api.crud.application import db_get_application
from api.crud.companies import db_get_company_by_internal_id
from api.dependencies.database import get_db
from api.dependencies.config import settings
from api.schemas.core.application import ApplicationRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


class AccessRightsLevel:

    def __init__(self, required_level: ApplicationRole) -> None:
        self.required_level = required_level

    @staticmethod
    async def get_current_application(
        token: Annotated[str, Depends(oauth2_scheme)], 
        db: AsyncSession = Depends(get_db)
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            client_id = payload.get('sub')
            if client_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        application = await db_get_application(db, client_id)
        if application is None:
            raise credentials_exception
        return application

    def has_required_level(self, role: ApplicationRole)->bool:
        role_hierarchy = {
            ApplicationRole.super_user: 100,
            ApplicationRole.company_admin: 50,
            ApplicationRole.company_user: 0,
        }
        if role not in role_hierarchy:
            raise ValueError(f'Role {role} not found in role hierarchy')
        else:
            return role_hierarchy[role] >= role_hierarchy[self.required_level]

    async def is_member_of_company(self, db, application, company_uuid: str)->bool:
        if application.role == ApplicationRole.super_user:
            return True
        elif not company_uuid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='No company_id in path, contact system admin'
            )
        else:
            db_company = await db_get_company_by_internal_id(
                db, application.company_id)
            return db_company.uuid == company_uuid

    async def __call__(
        self,
        token: Annotated[str, Depends(oauth2_scheme)], 
        db: AsyncSession = Depends(get_db),
        company_uuid: str=None,
    ):
        application = await self.get_current_application(token, db)

        has_access_to_company = await self.is_member_of_company(
            db, application, company_uuid)
        
        if not has_access_to_company:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not authorized'
            )

        if not self.has_required_level(application.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not enough permissions'
            )
        else:
            return application


super_user_level = AccessRightsLevel(ApplicationRole.super_user)
company_admin_level = AccessRightsLevel(ApplicationRole.company_admin)
company_user_level = AccessRightsLevel(ApplicationRole.company_user)


def create_access_token(
        data: dict, expires_delta: timedelta=None)->Tuple[str, datetime]:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt, expire
