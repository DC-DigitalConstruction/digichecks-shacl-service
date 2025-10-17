from io import BytesIO
import time

from fastapi import APIRouter, Depends, status, Security, HTTPException
import pandas as pd
import pyshacl
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from rdflib import Graph

from api.schemas.app.check import (
    CheckInSchema,
    CheckOutSchema,
    RuleSource,
    DataSchema,
    DataSetType,
    DSpaceCheckSchema,
    CheckResultSchema
)
from api.models import Check
from api.dependencies.security import company_user_level
from api.dependencies.database import get_db
from api.crud.check import (
    db_create_check,
    db_get_all_checks,
    db_get_check,
    db_update_check,
    db_delete_check
)
from api.crud.connector import db_get_connector, db_get_connector_by_internal_id
from api.crud.companies import db_get_company
from api.utils.api import get_ttl_rule
from api.utils.convertors import dataframe_to_xml, xml_to_graph, graph_to_json_ld


async def get_ttl_rule_based_on_rule(db: AsyncSession, db_check: Check) -> Graph:
    if db_check.rule_source == RuleSource.digichecks_hosted:
        ttl_rule = db_check.initialised_ttl_rule
    
    elif db_check.rule_source == RuleSource.api:
        db_connector = await db_get_connector_by_internal_id(db, db_check.connector_id)
        
        ttl_rule = get_ttl_rule(
            endpoint=db_check.rule,
            username=db_connector.username,
            password=db_connector.decrypt_password()
        )
    else:
        allowd_rules = ', '.join([rule.value for rule in RuleSource])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Rule source not supported, choose: {allowd_rules}'
        )

    return ttl_rule


def start_dspace_transfer_process(consumer_url: str, dataset_id: str):
    try:
        resp_transfer_process = requests.post(
            (f'http://{consumer_url}/api/management/v1/requests/transfer'
            f'/dataset/{dataset_id}'),
            headers={'Content-Type': 'application/json'},
        )
        resp_transfer_process.raise_for_status()
        time.sleep(5)
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Failed to start transfer process: {e}'
        )
    
    return resp_transfer_process.json()


def get_dspace_dataset(consumer_url: str, dataset_id: str, retry: int=5):
    def get_dspace_data(consumer_url: str, dataset_id: str):
        resp = requests.get(
            f'http://{consumer_url}/api/data-plane/v1/consumer/{dataset_id}'
        )
        resp.raise_for_status()
        return resp

    error_msg = 'Too many retries'
    while retry > 0:
        try:
            return get_dspace_data(consumer_url, dataset_id)
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            retry -= 1
            time.sleep(5)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Failed to start transfer process: {error_msg}'
    )