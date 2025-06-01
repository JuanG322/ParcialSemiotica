import os
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD

EX = Namespace("http://example.org/ontologia#")

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_graph(graph, filepath):
    try:
        graph.serialize(destination=filepath, format="turtle")
        print(f"Datos RDF guardados en: {filepath}")
    except Exception as e:
        print(f"Error al guardar el grafo en {filepath}: {e}")

def load_ontology(graph, ontology_path):
    if os.path.exists(ontology_path):
        try:
            graph.parse(ontology_path, format="turtle")
            print(f"Ontología cargada desde: {ontology_path}")
        except Exception as e:
            print(f"Error al cargar ontología: {e}")
    else:
        print(f"Advertencia: No se encontró la ontología en {ontology_path}")

def create_user_data(graph=None):
    if graph is None:
        graph = Graph()
        
    graph.bind("ex", EX)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("xsd", XSD)

    intereses_musicales = {
        "InteresPop": "Pop",
        "InteresRock": "Rock",
        "InteresElectronica": "Electrónica",
        "InteresRap": "Rap",
        "InteresReggaeton": "Reggaetón"
    }

    for interes_id, nombre_interes in intereses_musicales.items():
        interes_uri = EX[interes_id]
        graph.add((interes_uri, RDF.type, EX.Interes))
        graph.add((interes_uri, EX.nombreInteres, Literal(nombre_interes, datatype=XSD.string)))

    usuarios_data = [
        {"id": "usuario1", "nombre": "Ana Pérez", "edad": 28, "intereses_ids": ["InteresPop", "InteresElectronica"]},
        {"id": "usuario2", "nombre": "Luis Gómez", "edad": 34, "intereses_ids": ["InteresRock"]},
        {"id": "usuario3", "nombre": "Carlos Diaz", "edad": 22, "intereses_ids": ["InteresRap", "InteresReggaeton"]},
        {"id": "usuario4", "nombre": "Sofia Castro", "edad": 25, "intereses_ids": ["InteresRock", "InteresPop", "InteresElectronica"]},
        {"id": "usuario5", "nombre": "Juan Giraldo", "edad": 30, "intereses_ids": ["InteresReggaeton", "InteresElectronica"]},
    ]

    for user_data in usuarios_data:
        user_uri = EX[user_data["id"]]
        graph.add((user_uri, RDF.type, EX.Usuario))
        graph.add((user_uri, EX.nombreUsuario, Literal(user_data["nombre"], datatype=XSD.string)))
        graph.add((user_uri, EX.edad, Literal(user_data["edad"], datatype=XSD.integer)))

        for interes_id_str in user_data["intereses_ids"]:
            interes_uri_ref = EX[interes_id_str]
            graph.add((user_uri, EX.tieneInteres, interes_uri_ref))

    return graph

def create_content_data(graph=None):
    if graph is None:
        graph = Graph()
        
    graph.bind("ex", EX)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("xsd", XSD)

    generos_data = {
        "Pop": {"id": "GeneroPop", "nombre": "Pop"},
        "Rock": {"id": "GeneroRock", "nombre": "Rock"},
        "Electronica": {"id": "GeneroElectronica", "nombre": "Electrónica"},
        "Rap": {"id": "GeneroRap", "nombre": "Rap"},
        "Reggaeton": {"id": "GeneroReggaeton", "nombre": "Reggaetón"}
    }

    for genero_key, genero_info in generos_data.items():
        genero_uri = EX[genero_info["id"]]
        graph.add((genero_uri, RDF.type, EX.Genero))
        graph.add((genero_uri, EX.nombreGenero, Literal(genero_info["nombre"], datatype=XSD.string)))

    contenido_data = [
        {"id": "cancion1", "titulo": "Estrella Pop", "genero_id": "GeneroPop"},
        {"id": "cancion2", "titulo": "Rock Eterno", "genero_id": "GeneroRock"},
        {"id": "cancion3", "titulo": "Ritmo Digital", "genero_id": "GeneroElectronica"},
        {"id": "cancion4", "titulo": "Versos Callejeros", "genero_id": "GeneroRap"},
        {"id": "cancion5", "titulo": "Noche de Perreo", "genero_id": "GeneroReggaeton"},
        {"id": "cancion6", "titulo": "Sueños Pop", "genero_id": "GeneroPop"},
        {"id": "cancion7", "titulo": "Guitarra Rebelde", "genero_id": "GeneroRock"},
        {"id": "cancion8", "titulo": "Frecuencia Modulada", "genero_id": "GeneroElectronica"},
        {"id": "cancion9", "titulo": "Rimas y Verdades", "genero_id": "GeneroRap"},
        {"id": "cancion10", "titulo": "Baila Conmigo", "genero_id": "GeneroReggaeton"},
    ]

    for item_data in contenido_data:
        item_uri = EX[item_data["id"]]
        graph.add((item_uri, RDF.type, EX.Contenido))
        graph.add((item_uri, EX.titulo, Literal(item_data["titulo"], datatype=XSD.string)))
        genero_uri_ref = EX[item_data["genero_id"]]
        graph.add((item_uri, EX.perteneceAGenero, genero_uri_ref))

    return graph

def create_combined_data():
    combined_graph = Graph()
    combined_graph.bind("ex", EX)
    combined_graph.bind("rdf", RDF)
    combined_graph.bind("rdfs", RDFS)
    combined_graph.bind("xsd", XSD)
    ontology_path = os.path.join("semantica", "ontology.ttl")
    load_ontology(combined_graph, ontology_path)
    create_user_data(combined_graph)
    create_content_data(combined_graph)
    return combined_graph

if __name__ == "__main__":
    base_output_path = "semantica"
    ensure_dir(base_output_path)

    print("Generando datos RDF...")

    print("\n2. Creando archivo combinado...")
    combined_graph = create_combined_data()
    combined_filepath = os.path.join(base_output_path, "data.ttl")
    save_graph(combined_graph, combined_filepath)

    print(f"\nProceso completado!")
    print(f"- Archivo combinado: {combined_filepath}")
    print(f"- Total de triples en data.ttl: {len(combined_graph)}")
