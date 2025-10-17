from io import BytesIO
import time

from fastapi import APIRouter, Depends, status, Security, HTTPException
import pandas as pd
import pyshacl
import requests
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.app.check import (
    CheckInSchema,
    CheckOutSchema,
    RuleSource,
    DataSchema,
    DataSetType,
    DSpaceCheckSchema,
    CheckResultSchema
)
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
from api.utils.check_helpers import (
    get_ttl_rule_based_on_rule,
    get_dspace_dataset,
    start_dspace_transfer_process
)


check_router = APIRouter()


@check_router.post(
    name='Create new SHACL compliancy check rule',
    path='',
    status_code=status.HTTP_201_CREATED,
    response_model=CheckOutSchema,
    dependencies=[Security(company_user_level)]
)
async def create_check(
    company_uuid: str,
    check: CheckInSchema,
    db: AsyncSession=Depends(get_db)
):
    # When rule source is hosted a rule must be specified in the post request
    if check.rule_source == RuleSource.digichecks_hosted and not check.rule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Rule must be given when rule source is digichecks-service'
        )
    
    elif check.rule_source == RuleSource.api:
        if not check.connector_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Connector must be specified when using api as rule source'
            )
        db_connector = await db_get_connector(db, check.connector_id)
        connector_id = db_connector.id
    
    else:
        # If rule source is not api, connector is not needed
        connector_id = None
    
    db_company = await db_get_company(db, company_uuid)
    db_check = await db_create_check(db, check, db_company.id, connector_id)

    if db_check.rule_source == RuleSource.api:
        return CheckOutSchema(
            check_id=db_check.uuid,
            check_name=db_check.check_name,
            rule_source=db_check.rule_source,
            rule=db_check.rule,
            connector_id=db_connector.uuid
        )
    else:
        return db_check


@check_router.get(
    name='Get all SHACL compliancy check rules',
    path='/all',
    status_code=status.HTTP_200_OK,
    response_model=list[CheckOutSchema],
    dependencies=[Security(company_user_level)]
)
async def get_checks(
    company_uuid: str,
    db: AsyncSession=Depends(get_db)
):
    db_company = await db_get_company(db, company_uuid)
    db_checks = await db_get_all_checks(db, db_company.id)

    # Get the connectors to map the connector_id to the connector_uuid
    db_connectors = [
        await db_get_connector_by_internal_id(db, check.connector_id)
        for check 
        in db_checks 
        if check.connector_id
    ]
    connector_map = {connector.id: connector.uuid for connector in db_connectors}

    transformed_checks = [
        {
            **check.__dict__,
            'connector_id': connector_map.get(check.connector_id)
        }
        for check in db_checks
    ]

    return transformed_checks


@check_router.get(
    name='Get SHACL compliancy check rule',
    path='/{check_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=CheckOutSchema,
    dependencies=[Security(company_user_level)]
)
async def get_check(
    company_uuid: str,
    check_uuid: str,
    db: AsyncSession=Depends(get_db)
):
    db_check = await db_get_check(db, check_uuid)

    if db_check.rule_source == RuleSource.api:
        db_connector = await db_get_connector_by_internal_id(db, db_check.connector_id)
        return CheckOutSchema(
            check_id=db_check.uuid,
            check_name=db_check.check_name,
            rule_source=db_check.rule_source,
            rule=db_check.rule,
            connector_id=db_connector.uuid
        )
    else:
        return db_check


@check_router.put(
    name='Update SHACL compliancy check rule',
    path='/{check_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=CheckOutSchema,
    dependencies=[Security(company_user_level)]
)
async def update_check(
    company_uuid: str,
    check_uuid: str,
    check: CheckInSchema,
    db: AsyncSession=Depends(get_db)
):
    db_check = await db_get_check(db, check_uuid)
    db_check = await db_update_check(db, db_check, check)
    return db_check


@check_router.delete(
    name='Delete SHACL compliancy check rule',
    path='/{check_uuid}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(company_user_level)]
)
async def delete_check(
    company_uuid: str,
    check_uuid: str,
    db: AsyncSession=Depends(get_db)
):
    db_check = await db_get_check(db, check_uuid)
    await db_delete_check(db, db_check)
    return None


@check_router.post(
    name='Run SHACL compliancy check',
    path='/{check_uuid}/run',
    status_code=status.HTTP_200_OK,
    response_model=CheckResultSchema,
    dependencies=[Security(company_user_level)]
)
async def run_check(
    company_uuid: str,
    check_uuid: str,
    data: DataSchema,
    db: AsyncSession=Depends(get_db)
):
    db_check = await db_get_check(db, check_uuid)
    ttl_rule = await get_ttl_rule_based_on_rule(db, db_check)

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=data.as_ttl,
        shacl_graph=ttl_rule,
        ont_graph=ttl_rule,
        inference='none', # none or rdfs
        abort_on_first=False,
        allow_infos=False,
        allow_warnings=True,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False,
        serialize_report_graph='turtle'
    )

    check_result = CheckResultSchema(
        check_id=check_uuid,
        check_name=db_check.check_name,
        check_result='Pass' if conforms else 'Fail',
        description=results_text
    )
    return check_result


@check_router.post(
    name='Run Data Space SHACL compliancy check',
    path='/{check_uuid}/run/dspace',
    status_code=status.HTTP_200_OK,
    response_model=CheckResultSchema,
    dependencies=[Security(company_user_level)]
)
async def run_dspace_check(
    company_uuid: str,
    check_uuid: str,
    data: DSpaceCheckSchema,
    db: AsyncSession=Depends(get_db)
):
    db_check = await db_get_check(db, check_uuid)
    ttl_rule = await get_ttl_rule_based_on_rule(db, db_check)

    resp_transfer_process = start_dspace_transfer_process(
        consumer_url='51.138.27.252:8181',
        dataset_id=data.dataset_id
    )

    resp = get_dspace_dataset(
        consumer_url='51.138.27.252:8183',
        dataset_id=data.dataset_id
    )

    if data.data_set_type == DataSetType.EXCEL:
        df = pd.read_excel(BytesIO(resp.content))

        xml = dataframe_to_xml(
            df=df,
            col_mapping=data.col_mapping
        )

        turtle = xml_to_graph(
            xml=xml,
            namespaces=data.namespaces
        )

        json_ld = graph_to_json_ld(turtle)
    
    elif data.data_set_type == DataSetType.JSON_LD:
        json_ld = resp.json()

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Data set type must be either excel or JSON-LD'
        )

    data_schema = DataSchema(**json_ld)

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=data_schema.as_ttl,
        shacl_graph=ttl_rule,
        ont_graph=ttl_rule,
        inference='none', # none or rdfs
        abort_on_first=False,
        allow_infos=False,
        allow_warnings=True,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False,
        serialize_report_graph='turtle'
    )

    check_result = CheckResultSchema(
        check_id=check_uuid,
        check_name=db_check.check_name,
        check_result='Pass' if conforms else 'Fail',
        description=results_text
    )
    return check_result
