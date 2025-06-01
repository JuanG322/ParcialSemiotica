from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import sys
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from agentes.agente_perfil import AgentePerfilUsuario
    from agentes.agente_recomendacion import AgenteRecomendacion
    from agentes.utils import ConfiguracionRDF
    print("Agentes y ConfiguracionRDF importados correctamente")
except ImportError as e:
    print(f"Error: No se pueden importar los módulos necesarios: {e}")
    traceback.print_exc()
    sys.exit(1)

app = Flask(__name__)
app.secret_key = 'clave_secreta_simple_123'

agente_perfil = None
agente_recomendacion = None
rdf_config = None
main_graph = None

def inicializar_agentes_y_grafo():
    global agente_perfil, agente_recomendacion, rdf_config, main_graph

    if rdf_config is None:
        print("Inicializando ConfiguracionRDF...")
        rdf_config = ConfiguracionRDF()

    if main_graph is None:
        print("Cargando grafo RDF combinado...")
        try:
            main_graph = rdf_config.cargar_grafo_combinado()
            if main_graph is None or len(main_graph) == 0:
                print("Error crítico: El grafo RDF está vacío o no se pudo cargar.")
                print(f"ConfiguracionRDF base_path: {rdf_config.base_path if rdf_config else 'N/A'}")
                return False
            print(f"Grafo cargado con {len(main_graph)} triples.")
        except Exception as e:
            print(f"Excepción al cargar el grafo RDF: {e}")
            traceback.print_exc()
            return False

    if agente_perfil is None or agente_recomendacion is None:
        print("Inicializando agentes con grafo compartido...")
        try:
            agente_perfil = AgentePerfilUsuario(main_graph, rdf_config)
            agente_recomendacion = AgenteRecomendacion(main_graph, rdf_config)
            print("Agentes inicializados correctamente.")
        except Exception as e:
            print(f"Excepción al inicializar agentes: {e}")
            traceback.print_exc()
            return False
    return True

@app.route('/')
def index():
    if not (agente_perfil and agente_recomendacion and main_graph is not None and len(main_graph) > 0) :
        if not inicializar_agentes_y_grafo():
            return "Error: No se pudieron inicializar los agentes o cargar el grafo RDF. Verifique los logs del servidor.", 500

    usuarios = []
    try:
        usuarios = agente_perfil.obtener_usuarios_disponibles()
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        traceback.print_exc()

    usuario_actual = None
    if 'usuario_uri' in session:
        try:
            usuario_info = agente_perfil.obtener_info_usuario(session['usuario_uri'])
            if usuario_info:
                usuario_actual = {
                    'uri': session['usuario_uri'],
                    'nombre': usuario_info['nombre'],
                    'edad': usuario_info['edad']
                }
        except Exception as e:
            print(f"Error obteniendo info usuario: {e}")
            traceback.print_exc()
            session.pop('usuario_uri', None)

    return render_template('index.html', 
                         usuarios=usuarios, 
                         usuario_actual=usuario_actual)

@app.route('/seleccionar_usuario', methods=['POST'])
def seleccionar_usuario():
    if not agente_perfil:
        return jsonify({'success': False, 'message': 'Error del servidor: Agente de perfil no inicializado.'}), 500
    try:
        usuario_uri = request.form.get('usuario_uri')
        if usuario_uri:
            session['usuario_uri'] = usuario_uri
            return jsonify({'success': True, 'message': 'Usuario seleccionado correctamente'})
        else:
            return jsonify({'success': False, 'message': 'Debe seleccionar un usuario válido'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/obtener_cancion_para_calificar')
def obtener_cancion_para_calificar():
    if not agente_perfil:
        return jsonify({'success': False, 'message': 'Error del servidor: Agente de perfil no inicializado.'}), 500
    if 'usuario_uri' not in session:
        return jsonify({'success': False, 'message': 'No hay usuario seleccionado'})

    try:
        usuario_uri = session['usuario_uri']
        resultado = agente_perfil.mostrar_cancion_para_calificar(usuario_uri)

        if isinstance(resultado, tuple) and len(resultado) == 2:
            cancion_data, mensaje = resultado
            if mensaje:
                return jsonify({'success': False, 'message': mensaje})

            cancion_uri, titulo, genero = cancion_data
            return jsonify({
                'success': True,
                'cancion': {
                    'uri': str(cancion_uri),
                    'titulo': titulo,
                    'genero': genero
                }
            })
        else:
            print(f"Resultado inesperado de mostrar_cancion_para_calificar: {resultado}")
            return jsonify({'success': False, 'message': 'No se pudo obtener canción para calificar (formato inesperado)'})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

@app.route('/calificar_cancion', methods=['POST'])
def calificar_cancion():
    if not agente_perfil:
        return jsonify({'success': False, 'message': 'Error del servidor: Agente de perfil no inicializado.'}), 500
    if 'usuario_uri' not in session:
        return jsonify({'success': False, 'message': 'No hay usuario seleccionado'})

    try:
        data = request.get_json()
        cancion_uri = data.get('cancion_uri')
        le_gusta = data.get('le_gusta')

        if cancion_uri is None or le_gusta is None:
            return jsonify({'success': False, 'message': 'Datos incompletos'})

        usuario_uri = session['usuario_uri']
        resultado = agente_perfil.registrar_calificacion(usuario_uri, cancion_uri, le_gusta)

        return jsonify({
            'success': True,
            'message': resultado
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

@app.route('/obtener_recomendaciones')
def obtener_recomendaciones():
    if not agente_recomendacion:
        return jsonify({'success': False, 'message': 'Error del servidor: Agente de recomendación no inicializado.'}), 500
    if 'usuario_uri' not in session:
        return jsonify({'success': False, 'message': 'No hay usuario seleccionado'})

    try:
        usuario_uri = session['usuario_uri']
        recomendaciones = agente_recomendacion.obtener_recomendaciones(usuario_uri, 5)

        return jsonify({
            'success': True,
            'recomendaciones': [
                {
                    'uri': str(uri),
                    'titulo': titulo,
                    'genero': genero
                } for uri, titulo, genero in recomendaciones
            ]
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

@app.route('/actualizar_intereses', methods=['POST'])
def actualizar_intereses():
    if not agente_perfil:
        return jsonify({'success': False, 'message': 'Error del servidor: Agente de perfil no inicializado.'}), 500
    if 'usuario_uri' not in session:
        return jsonify({'success': False, 'message': 'No hay usuario seleccionado'})

    try:
        usuario_uri = session['usuario_uri']
        resultado = agente_perfil.actualizar_intereses(usuario_uri)

        return jsonify({
            'success': True,
            'message': resultado
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

@app.route('/obtener_estadisticas')
def obtener_estadisticas():
    if not agente_perfil:
        return jsonify({'success': False, 'message': 'Error del servidor: Agente de perfil no inicializado.'}), 500
    if 'usuario_uri' not in session:
        return jsonify({'success': False, 'message': 'No hay usuario seleccionado'})

    try:
        usuario_uri = session['usuario_uri']
        stats = agente_perfil.obtener_estadisticas_usuario(usuario_uri)
        intereses = agente_perfil.obtener_intereses_usuario(usuario_uri)
        calificaciones = agente_perfil.obtener_calificaciones_usuario(usuario_uri)

        return jsonify({
            'success': True,
            'estadisticas': stats,
            'intereses': intereses,
            'calificaciones_recientes': [
                {
                    'titulo': titulo,
                    'genero': genero,
                    'valor': valor,
                    'fecha': str(fecha) 
                } for _, titulo, genero, valor, fecha in calificaciones[:5]
            ]
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

@app.route('/guardar_cambios', methods=['POST'])
def guardar_cambios():
    if not agente_perfil:
        return jsonify({'success': False, 'message': 'Error del servidor: Agente de perfil no inicializado.'}), 500
    try:
        resultado = agente_perfil.guardar_cambios()
        return jsonify({
            'success': True,
            'message': resultado
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario_uri', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("=" * 50)
    print("Sistema de Recomendación Musical")
    print("=" * 50)

    if inicializar_agentes_y_grafo():
        print("Servidor Flask listo y escuchando en: http://localhost:5000 (o http://0.0.0.0:5000)")
        print("Presiona Ctrl+C para detener el servidor.")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Error crítico: No se pudo iniciar la aplicación Flask debido a problemas con la inicialización de agentes o carga del grafo RDF.")
        print("Por favor, revise los mensajes de error anteriores.")
