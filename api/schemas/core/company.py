from datetime import datetime

from pydantic import BaseModel, Field


class CompanyInSchema(BaseModel):
    name: str = Field(min_length=3, max_length=100)


class CompanyOutSchema(BaseModel):
    uuid: str = Field(alias='company_id')
    name: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
        populate_by_name = True
