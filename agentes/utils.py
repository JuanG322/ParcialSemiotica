import os
from rdflib import Graph, Namespace

class ConfiguracionRDF:
    
    def __init__(self):
        self.ex = Namespace("http://example.org/ontologia#")
        current_dir = os.path.dirname(__file__)
        if 'agentes' in current_dir:
            self.base_path = os.path.join(os.path.dirname(current_dir), 'semantica')
        else:
            self.base_path = os.path.join(current_dir, 'semantica')
        
    def cargar_grafo_combinado(self):
        graph = Graph()
        graph.bind("ex", self.ex)
        
        ontology_path = os.path.join(self.base_path, 'ontology.ttl')
        if os.path.exists(ontology_path):
            try:
                graph.parse(ontology_path, format='turtle')
                print(f"✓ Ontología cargada desde: {ontology_path}")
            except Exception as e:
                print(f"❌ Error cargando ontología: {e}")
        else:
            print(f"⚠️ No se encontró ontología en: {ontology_path}")
                
        data_path = os.path.join(self.base_path, 'data.ttl')
        if os.path.exists(data_path):
            try:
                graph.parse(data_path, format='turtle')
                print(f"✓ Datos cargados desde: {data_path}")
            except Exception as e:
                print(f"❌ Error cargando datos: {e}")
        else:
            print(f"⚠️ No se encontró data.ttl en: {data_path}")
        
        if len(graph) == 0:
            print("⚠️ El grafo está vacío. Verificar rutas de archivos.")
            print(f"Directorio actual: {os.getcwd()}")
            print(f"Ruta base calculada: {self.base_path}")
        else:
            print(f"✓ Grafo cargado con {len(graph)} triples")
            
        return graph
    
    def guardar_datos_actualizados(self, graph):
        os.makedirs(self.base_path, exist_ok=True)
        output_path = os.path.join(self.base_path, 'datos_actualizados.ttl')
        try:
            graph.serialize(destination=output_path, format='turtle')
            print(f"✓ Datos guardados en: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Error guardando datos: {e}")
            return None
