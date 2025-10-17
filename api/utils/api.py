from fastapi import HTTPException, status
import requests
import rdflib


def get_ttl_rule(
        endpoint: str,
        username: str,
        password: str
)->rdflib.Graph:
    try:
        resp = requests.get(
            endpoint,
            auth=(username, password),
            headers={'Accept': 'text/turtle'}
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error connecting to API: {e}'
        )

    # Parse the response into a graph
    try:
        graph = rdflib.Graph()
        graph.parse(data=resp.text, format='turtle')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error parsing response into graph: {e}'
        )

    return graph
