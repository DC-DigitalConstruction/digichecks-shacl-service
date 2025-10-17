from fastapi import FastAPI

from api.dependencies.config import settings
from api.routers.application_router import router as applications_router
from api.routers.auth_router import router as auth_router
from api.routers.company_router import router as companies_router
from api.routers.check_router import check_router
from api.routers.connector_router import connector_router
from api.routers.convertor_router import router as convertor_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


tags_metadata = [
    {
        'name': 'Token', 
        'description': 'Retrieving a token'
    },
    {
        'name': 'Company', 
        'description': 'Requests to create, read, update and delete companies'
    },
    {
        'name': 'Client Application', 
        'description': 'Requests to create an application'
    },
    {
        'name': 'Check', 
        'description': 'Requests to create a check'
    },
    {
        'name': 'API Connector', 
        'description': 'Requests to create, read, update and delete API connectors'
    },
    {
        'name': 'Convertors', 
        'description': 'Convert specific datasets to JSON-LD'
    }
]

app.openapi_tags = tags_metadata

app.include_router(
    auth_router, prefix='/auth', tags=['Token'])
app.include_router(
    companies_router, prefix='/company', tags=['Company'])
app.include_router(
    applications_router, prefix='/company/{company_uuid}/application', tags=['Client Application'])
app.include_router(
    check_router, prefix='/company/{company_uuid}/check', tags=['Check'])
app.include_router(
    connector_router, prefix='/company/{company_uuid}/connector', tags=['API Connector'])
app.include_router(
    convertor_router, prefix='/company/{company_uuid}/convert', tags=['Convert Excel to JSON-LD'])
