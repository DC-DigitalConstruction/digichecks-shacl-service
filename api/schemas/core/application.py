from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class ApplicationRole(str, Enum):
    super_user = 'super_user'
    company_admin = 'company_admin'
    company_user = 'company_user'


class ApplicatitonInSchema(BaseModel):
    role: ApplicationRole = ApplicationRole.company_user


class ApplicatitonInDBSchema(ApplicatitonInSchema):
    company_id: int
    client_id: UUID
    hashed_client_secret: str


class ApplicationOutSchema(BaseModel):
    client_id: UUID
    client_secret: str

    class Config:
        from_attributes = True
