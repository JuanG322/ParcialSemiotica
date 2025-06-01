from rdflib import Graph, Namespace, URIRef, Literal, RDF
from rdflib.namespace import XSD
from datetime import datetime
import random
from .utils import ConfiguracionRDF

class AgentePerfilUsuario:
    
    def __init__(self, graph: Graph, config: ConfiguracionRDF):
        self.graph = graph
        self.config = config
        self.ex = self.config.ex
        
    def obtener_usuarios_disponibles(self):
        query = """
        PREFIX ex: <http://example.org/ontologia#>
        
        SELECT ?usuario ?nombre
        WHERE {
            ?usuario a ex:Usuario ;
                     ex:nombreUsuario ?nombre .
        }
        ORDER BY ?nombre
        """
        
        resultados = list(self.graph.query(query))
        return [(str(result[0]), str(result[1])) for result in resultados]
    
    def obtener_info_usuario(self, usuario_uri):
        query = f"""
        PREFIX ex: <http://example.org/ontologia#>
        
        SELECT ?nombre ?edad
        WHERE {{
            <{usuario_uri}> ex:nombreUsuario ?nombre ;
                           ex:edad ?edad .
        }}
        """
        
        resultado = list(self.graph.query(query))
        if resultado:
            return {'nombre': str(resultado[0][0]), 'edad': int(resultado[0][1])}
        return None
        
    def mostrar_cancion_para_calificar(self, usuario_uri):
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
                ?cal ex:sobreContenido ?cancion .
            }}
        }}
        """
        
        resultados = list(self.graph.query(query))
        
        if not resultados:
            return None, "¡Has calificado todas las canciones disponibles!"
        
        cancion_data = random.choice(resultados)
        return cancion_data, None
    
    def registrar_calificacion(self, usuario_uri, cancion_uri, le_gusta):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        calificacion_id = f"calificacion_{abs(hash(str(usuario_uri) + str(cancion_uri)))}_{timestamp}_{random_suffix}"
        calificacion_uri = self.ex[calificacion_id]
        valor = 5 if le_gusta else 2
        
        cancion_existe = list(self.graph.triples((URIRef(cancion_uri), RDF.type, self.ex.Contenido)))
        if not cancion_existe:
            return "Error: La canción no existe en el sistema"
        
        calificacion_previa = f"""
        PREFIX ex: <http://example.org/ontologia#>
        ASK {{
            <{usuario_uri}> ex:realizaCalificacion ?cal .
            ?cal ex:sobreContenido <{cancion_uri}> .
        }}
        """
        
        if self.graph.query(calificacion_previa).askAnswer:
            return "Ya has calificado esta canción anteriormente"
        
        self.graph.add((calificacion_uri, RDF.type, self.ex.Calificacion))
        self.graph.add((calificacion_uri, self.ex.valorCalificacion, Literal(valor, datatype=XSD.integer)))
        self.graph.add((calificacion_uri, self.ex.fechaCalificacion, Literal(datetime.now(), datatype=XSD.dateTime)))
        self.graph.add((URIRef(usuario_uri), self.ex.realizaCalificacion, calificacion_uri))
        self.graph.add((calificacion_uri, self.ex.sobreContenido, URIRef(cancion_uri)))
        
        return f"✓ Calificación registrada: {'Me gusta' if le_gusta else 'No me gusta'}"
        
    def actualizar_intereses(self, usuario_uri):
        query = f"""
        PREFIX ex: <http://example.org/ontologia#>
        
        SELECT ?genero (AVG(?valor) as ?promedio) (COUNT(?valor) as ?total)
        WHERE {{
            <{usuario_uri}> ex:realizaCalificacion ?cal .
            ?cal ex:valorCalificacion ?valor ;
                 ex:sobreContenido ?cancion .
            ?cancion ex:perteneceAGenero ?generoUri .
            ?generoUri ex:nombreGenero ?genero .
            FILTER(?valor >= 4)
        }}
        GROUP BY ?genero
        HAVING (COUNT(?valor) >= 1)
        ORDER BY DESC(?promedio)
        """
        
        resultados = list(self.graph.query(query))
        
        for triple in list(self.graph.triples((URIRef(usuario_uri), self.ex.tieneInteres, None))):
            self.graph.remove(triple)
        
        intereses_agregados = []
        for resultado in resultados[:3]:
            genero_nombre = str(resultado[0])
            interes_nombre_norm = (genero_nombre.replace('ó', 'o')
                                         .replace('é', 'e')
                                         .replace('ñ', 'n')
                                         .replace('á', 'a')
                                         .replace('í', 'i')
                                         .replace('ú', 'u')
                                         .replace(' ', '')
                                         .capitalize())
            interes_uri = self.ex[f"Interes{interes_nombre_norm}"]
            
            if not list(self.graph.triples((interes_uri, RDF.type, self.ex.Interes))):
                self.graph.add((interes_uri, RDF.type, self.ex.Interes))
                self.graph.add((interes_uri, self.ex.nombreInteres, Literal(genero_nombre, datatype=XSD.string)))
            
            self.graph.add((URIRef(usuario_uri), self.ex.tieneInteres, interes_uri))
            intereses_agregados.append(genero_nombre)
            
        if not intereses_agregados:
            return "No hay suficientes calificaciones positivas para actualizar intereses"
            
        return f"✓ Intereses actualizados: {', '.join(intereses_agregados)}"
    
    def obtener_estadisticas_usuario(self, usuario_uri):
        query = f"""
        PREFIX ex: <http://example.org/ontologia#>
        
        SELECT 
            (COUNT(?cal) as ?total_calificaciones)
            (AVG(?valor) as ?promedio_calificaciones)
            (COUNT(DISTINCT ?genero) as ?generos_calificados)
        WHERE {{
            <{usuario_uri}> ex:realizaCalificacion ?cal .
            ?cal ex:valorCalificacion ?valor ;
                 ex:sobreContenido ?cancion .
            ?cancion ex:perteneceAGenero ?generoUri .
            ?generoUri ex:nombreGenero ?genero .
        }}
        """
        
        resultado = list(self.graph.query(query))
        if resultado and resultado[0] and resultado[0][0] is not None:
            total, promedio, generos = resultado[0]
            return {
                'total_calificaciones': int(total) if total else 0,
                'promedio_calificaciones': float(promedio) if promedio else 0.0,
                'generos_calificados': int(generos) if generos else 0
            }
        return {'total_calificaciones': 0, 'promedio_calificaciones': 0.0, 'generos_calificados': 0}
    
    def obtener_intereses_usuario(self, usuario_uri):
        query = f"""
        PREFIX ex: <http://example.org/ontologia#>
        
        SELECT ?nombreInteres
        WHERE {{
            <{usuario_uri}> ex:tieneInteres ?interes .
            ?interes ex:nombreInteres ?nombreInteres .
        }}
        """
        
        resultados = list(self.graph.query(query))
        return [str(resultado[0]) for resultado in resultados]
    
    def obtener_calificaciones_usuario(self, usuario_uri):
        query = f"""
        PREFIX ex: <http://example.org/ontologia#>
        
        SELECT ?cancion ?titulo ?genero ?valor ?fecha
        WHERE {{
            <{usuario_uri}> ex:realizaCalificacion ?cal .
            ?cal ex:sobreContenido ?cancion ;
                 ex:valorCalificacion ?valor ;
                 ex:fechaCalificacion ?fecha .
            ?cancion ex:titulo ?titulo ;
                     ex:perteneceAGenero ?generoUri .
            ?generoUri ex:nombreGenero ?genero .
        }}
        ORDER BY DESC(?fecha)
        """
        
        resultados = list(self.graph.query(query))
        return [(str(r[0]), str(r[1]), str(r[2]), int(r[3]), str(r[4])) for r in resultados]
    
    def guardar_cambios(self):
        output_path = self.config.guardar_datos_actualizados(self.graph)
        if output_path:
            return f"✓ Cambios guardados en {output_path}"
        else:
            return "❌ Error al guardar cambios"