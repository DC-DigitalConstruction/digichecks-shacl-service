from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import create_access_token, get_db, settings
from api.crud.application import db_get_application
from api.utils.oauth_form import CustomOAuth2PasswordRequestForm
from api.utils.hash import verify_password
from api.schemas import TokenSchema


router = APIRouter()


@router.post(
    name='Get access token',
    path='/token',
    status_code=status.HTTP_201_CREATED,
    response_model=TokenSchema
)
async def get_token(
    form_data: CustomOAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    application = await db_get_application(db, form_data.client_id)

    if not verify_password(form_data.client_secret, application.hashed_client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect client_id or client_secret',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, expire = create_access_token(
        data={'sub': str(application.client_id)}, expires_delta=access_token_expires
    )

    return TokenSchema(access_token=access_token, expires_at=expire)
