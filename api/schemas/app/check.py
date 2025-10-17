import datetime as dt
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field
import rdflib
from fastapi import HTTPException, status


class RuleSource(str,Enum):
    digichecks_hosted = 'digichecks_hosted'
    api = 'api'


class CheckResult(str,Enum):
    PASS = 'Pass'
    FAIL = 'Fail'


class DataSetType(str,Enum):
    EXCEL = 'excel'
    JSON_LD = 'JSON-LD'


class CheckInSchema(BaseModel):
    check_name: str
    rule_source: RuleSource = RuleSource.digichecks_hosted
    rule: str
    connector_id: str=None


class CheckOutSchema(BaseModel):
    uuid: str = Field(alias='check_id')
    check_name: str
    rule_source: RuleSource
    rule: str
    connector_id: str=None

    class Config:
        from_attributes = True
        populate_by_name = True


class CheckResultSchema(BaseModel):
    check_id: str
    check_name: str
    check_result: CheckResult
    description: str = None
    timestamp: dt.datetime = dt.datetime.now()


class DataSchema(BaseModel):
    context: list = Field(alias='@context')
    graph: List[Any] = Field(alias='@graph')

    @property
    def as_ttl(self)->str:
        graph = rdflib.Graph()
        graph.parse(data=self.model_dump(by_alias=True), format='json-ld')
        ttl = graph.serialize(format='turtle')
        return ttl


class DSpaceCheckSchema(BaseModel):
    dataset_id: str
    data_set_type: DataSetType
    col_mapping: Optional[dict[str,str]] = None
    namespaces: Optional[dict[str,str]] = None

    @staticmethod
    def json_ld_to_ttl(json_ld)->str:
        graph = rdflib.Graph()
        graph.parse(data=json_ld, format='json-ld')
        ttl = graph.serialize(format='turtle')

        if not ttl.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='JSON-LD could not be converted to ttl, are you sure the JSON-LD is correct?'
            )

        return ttl
