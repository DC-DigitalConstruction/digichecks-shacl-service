import os
import subprocess
from typing import Dict
from xml.etree import ElementTree as ET

import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF
import json


def dataframe_to_xml(df: pd.DataFrame, col_mapping: Dict[str,str])->ET.ElementTree:
    root = ET.Element('root')
    for _, row in df.iterrows():
        element = ET.SubElement(root, 'row')
        for df_col, xml_col in col_mapping.items():
            ET.SubElement(element, xml_col).text = str(row.get(df_col, 'N/A'))

    return ET.ElementTree(root)


def xml_to_graph(xml: ET.ElementTree, namespaces: Dict[str,str])->Graph:
    temp_dir = 'temp'
    current_dir = os.path.dirname(__file__)

    jar_path = os.path.join(current_dir, 'sparql-anything-0.9.0.jar')
    query_path = os.path.join(current_dir, 'supplyPointQuery.sparql')
    
    # Create temp directory for the xml data
    os.makedirs(os.path.join(current_dir, temp_dir), exist_ok=True)
    xml_path = os.path.join(current_dir, temp_dir, 'supplyPoint.xml')
    xml.write(xml_path, encoding='utf-8', xml_declaration=True)

    # Run the conversion
    command = f'java -jar {jar_path} -q {query_path} -v uri=""{xml_path}""'
    result = subprocess.run(command, shell=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError(f'Error running the conversion: {result.stderr}')
    
    # Clean up
    os.remove(xml_path)
    os.rmdir(os.path.join(current_dir, temp_dir))

    # Parse the result to a graph
    graph = Graph()
    graph.parse(data=result.stdout, format='turtle')

    # Bind and define the namespaces
    for name, uri in namespaces.items():
        graph.bind(name, Namespace(uri))

    return graph


def graph_to_json_ld(graph: Graph)->str:
    jsonld_data = {
        '@context': [
            'https://stdigichecksprod.blob.core.windows.net/public/REALIA_context.jsonld',
            'https://stdigichecksprod.blob.core.windows.net/public/digiChecks_topLevelPermitOntology_context.jsonld'
        ],
        '@graph': []
    }
    sml = Namespace('https://w3id.org/sml/def#')

    for s in graph.subjects():
        rdf_type = graph.value(s, RDF.type)
        if rdf_type:
            # Use graph.qname() to get prefixed names
            node = {
                '@id': graph.qname(s),
                '@type': graph.qname(rdf_type),
                'quantitativeProperties': {},
                'nonQuantitativeProperties': {},
                'relations': {}
            }
            
            for p, o in graph.predicate_objects(s):
                # Skip RDF.type as it's already handled
                if p == RDF.type:
                    continue
                    
                value_triples = list(graph.triples((o, RDF.value, None)))
                if value_triples:
                    value = value_triples[0][2].value
                    unit = graph.value(o, sml.hasUnit)
                    unit_str = graph.qname(unit) if unit else None
                    
                    # Use qname for predicate
                    node['quantitativeProperties'][graph.qname(p)] = {
                        'value': value,
                        'hasUnit': unit_str
                    }
                else:
                    # Handle relations, using qname for both predicate and object
                    if isinstance(o, URIRef):  # Only convert URIs to qname
                        node['relations'][graph.qname(p)] = graph.qname(o)
                    else:
                        node['relations'][graph.qname(p)] = str(o)
                        
            jsonld_data['@graph'].append(node)
        
    return jsonld_data
