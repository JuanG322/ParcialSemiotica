from rdflib import Graph, Namespace, URIRef, Literal, RDF
from rdflib.namespace import XSD
from datetime import datetime
import random
from .utils import ConfiguracionRDF

class AgenteRecomendacion:
    
    def __init__(self, graph: Graph, config: ConfiguracionRDF):
        self.graph = graph
        self.config = config
        self.ex = self.config.ex

    def obtener_recomendaciones(self, usuario_uri, num_recomendaciones=3):
        query = f"""
        PREFIX ex: <http://example.org/ontologia#>
        
        SELECT DISTINCT ?cancion ?titulo ?genero ?interes
        WHERE {{
            <{usuario_uri}> ex:tieneInteres ?interes .
            ?interes ex:nombreInteres ?nombreInteres .
            ?cancion a ex:Contenido ;
                     ex:titulo ?titulo ;
                     ex:perteneceAGenero ?generoUri .
            ?generoUri ex:nombreGenero ?genero .
            FILTER(CONTAINS(LCASE(?nombreInteres), LCASE(?genero)) || 
                   CONTAINS(LCASE(?genero), LCASE(?nombreInteres)))
            FILTER NOT EXISTS {{
                <{usuario_uri}> ex:realizaCalificacion ?cal .
                ?cal ex:sobreContenido ?cancion ;
                     ex:valorCalificacion ?valorCal .
                FILTER(?valorCal < 3)
            }}
        }}
        """

        resultados_interes = list(self.graph.query(query))
        recomendaciones_finales = []
        canciones_vistas_uris = set()
        for r in resultados_interes:
            if str(r[0]) not in canciones_vistas_uris:
                recomendaciones_finales.append((str(r[0]), str(r[1]), str(r[2])))
                canciones_vistas_uris.add(str(r[0]))

        if len(recomendaciones_finales) < num_recomendaciones:
            num_faltantes = num_recomendaciones - len(recomendaciones_finales)
            recomendaciones_fallback = self._recomendaciones_fallback(usuario_uri, num_faltantes, canciones_vistas_uris)
            recomendaciones_finales.extend(recomendaciones_fallback)

        random.shuffle(recomendaciones_finales)
        return recomendaciones_finales[:num_recomendaciones]

    def _recomendaciones_fallback(self, usuario_uri, num_recomendaciones, excluir_uris=None):
        if excluir_uris is None:
            excluir_uris = set()

        query = f"""
        PREFIX ex: <http://example.org/ontologia#>
        
        SELECT DISTINCT ?cancion ?titulo ?genero
        WHERE {{
            ?cancion a ex:Contenido ;
                     ex:titulo ?titulo ;
                     ex:perteneceAGenero ?generoUri .
            ?generoUri ex:nombreGenero ?genero .
            FILTER NOT EXISTS {{
                <{usuario_uri}> ex:realizaCalificacion ?cal .
                ?cal ex:sobreContenido ?cancion ;
                     ex:valorCalificacion ?valorCal .
                FILTER(?valorCal < 3) 
            }}
            FILTER(?cancion NOT IN ({', '.join([f'<{uri}>' for uri in excluir_uris]) if excluir_uris else ''}))
        }}
        """

        resultados = list(self.graph.query(query))
        recomendaciones_filtradas = []
        for r in resultados:
            if str(r[0]) not in excluir_uris:
                recomendaciones_filtradas.append((str(r[0]), str(r[1]), str(r[2])))

        random.shuffle(recomendaciones_filtradas)
        return recomendaciones_filtradas[:num_recomendaciones]
