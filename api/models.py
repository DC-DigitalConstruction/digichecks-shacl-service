from cryptography.fernet import Fernet
import rdflib
from sqlalchemy import Column, String, Integer, ForeignKey, UUID
from sqlalchemy import Enum as SQLAlchemyEnum

from api.dependencies.database import (
    APPLICATION_TABLE,
    BaseModel,
    CHECK_TABLE, 
    COMPANY_TABLE,
    CONNECTOR_TABLE,
)
from api.schemas.app.check import RuleSource
from api.schemas.core.application import ApplicationRole
from api.dependencies import settings


class Company(BaseModel):
    __tablename__ = COMPANY_TABLE.table_name
    __table_args__ = {"schema": COMPANY_TABLE.schema_name}
    __id_prefix__ = 'co'

    name = Column(String, index=True, nullable=False)


class Application(BaseModel):
    __tablename__ = APPLICATION_TABLE.table_name
    __table_args__ = {'schema': APPLICATION_TABLE.schema_name}
    __id_prefix__ = 'ap'

    # Columns
    client_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    hashed_client_secret = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(ApplicationRole), nullable=False)

    # Foreign Keys
    company_id = Column(
        Integer,
        ForeignKey(COMPANY_TABLE.identifier),
        index=True,
        nullable=False
    )


class Check(BaseModel):
    __tablename__ = CHECK_TABLE.table_name
    __table_args__ = {'schema': CHECK_TABLE.schema_name}
    __id_prefix__ = 'ch'

    check_name = Column(String, index=True, nullable=False)
    rule_source = Column(SQLAlchemyEnum(RuleSource), nullable=False)
    rule = Column(String)

    # Foreign Keys
    connector_id = Column(
        Integer, 
        ForeignKey(CONNECTOR_TABLE.identifier),
        nullable=True
    )
    company_id = Column(
        Integer,
        ForeignKey(COMPANY_TABLE.identifier),
        index=True,
        nullable=False
    )

    @property
    def initialised_ttl_rule(self)->rdflib.Graph:
        graph = rdflib.Graph()
        graph.parse(data=self.rule, format='turtle')
        return graph

#TODO: Reset migrations and re-run them!!!
class Connector(BaseModel):
    __tablename__ = CONNECTOR_TABLE.table_name
    __table_args__ = {'schema': CONNECTOR_TABLE.schema_name}
    __id_prefix__ = 'cn'

    connector_name = Column(String, index=False, nullable=False)
    token_endpoint = Column(String, index=False, nullable=True)
    username = Column(String, index=False, nullable=False)
    password = Column(String, index=False, nullable=False)

    # Foreign Keys
    company_id = Column(
        Integer,
        ForeignKey(COMPANY_TABLE.identifier),
        index=True,
        nullable=False
    )

    def encrypt_password(self)->str:
        # Encrypt the password (encoding is required for the encryption, 
        # whereas the database is expecting a string. Hence the decoding)
        fernet = Fernet(settings.FERNET_KEY)
        return fernet.encrypt(self.password.encode()).decode()

    def decrypt_password(self)->str:
        fernet = Fernet(settings.FERNET_KEY)
        return fernet.decrypt(self.password.encode()).decode()
