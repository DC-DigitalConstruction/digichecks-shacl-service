from pydantic import BaseModel, Field


class ConnectorInSchema(BaseModel):
    connector_name: str
    username: str
    password: str
    token_endpoint: str=None


class ConnectorUpdateSchema(BaseModel):
    connector_name: str=None
    username: str=None
    password: str=None
    token_endpoint: str=None


class ConnectorOutSchema(BaseModel):
    uuid: str = Field(alias='connector_id')
    connector_name: str
    username: str
    token_endpoint: str | None

    class Config:
        from_attributes = True
        populate_by_name = True
