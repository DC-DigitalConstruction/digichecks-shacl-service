from io import BytesIO

from fastapi import APIRouter, Depends, status, Security, File, UploadFile
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from api.crud.companies import (
    db_create_company,
    db_get_company,
    db_update_company,
    db_delete_company
)
from api.dependencies import (
    get_db,
    super_user_level,
    company_admin_level, 
    company_user_level
)
from api.schemas import CompanyInSchema, CompanyOutSchema
from api.utils.convertors import dataframe_to_xml, xml_to_graph, graph_to_json_ld


router = APIRouter()


@router.post(
    name='Convert Realia Electricity Excel to JSON-LD',
    path='/realia/electricity',
    status_code=status.HTTP_201_CREATED,
    dependencies=[Security(company_user_level)]
)
async def convert_electricity_excel(
    file: UploadFile,
    db: AsyncSession = Depends(get_db)
):
    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        return {'message': f'Error reading Excel file: {e}'}
    
    xml = dataframe_to_xml(
        df=df,
        col_mapping={
            'CGP': 'CGP',
            'CGP Type': 'CGPType',
            'LGA': 'LGA',
            'Portal': 'Portal',
            'Planta': 'Planta',
            'Mano': 'Mano',
            'Supply Point Name': 'SupplyPointName',
            'Tipo Suministro': 'Tipo',
            'Potencia': 'Potencia',
            'Potencia Simultanea': 'PotenciaSimultánea',
        }
    )
    
    turtle = xml_to_graph(
        xml=xml,
        namespaces={
            'ex': 'http://example.org/realia/dataset/',
            'realia_otl': 'http://realia.es/realia-otl/',
            'realia_ds': 'http://realia-dataspace.org/data/',
            'qudt': 'http://qudt.org/schema/qudt/',
            'sml': 'https://w3id.org/sml/def#',
        }
    )

    json_ld = graph_to_json_ld(turtle)

    return json_ld
