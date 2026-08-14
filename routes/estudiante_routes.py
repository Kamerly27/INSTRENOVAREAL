from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from database.db import db
from models.usuario import Usuario
from models.matricula import Matricula
from models.modulo import Modulo
from models.material import Material
from models.foro import Foro
from models.comentario_foro import ComentarioForo
from models.actividad import Actividad
from models.examen import Examen
from models.calificacion import Calificacion
from models.mensaje import Mensaje
from models.certificado import Certificado
from models.entrega_actividad import EntregaActividad
from models.calificacion_entrega import CalificacionEntrega


estudiante = Blueprint(
    'estudiante',
    __name__,
    url_prefix='/estudiante'
)


@estudiante.route('/dashboard')
@login_required
def dashboard():

    matriculas = Matricula.query.filter_by(
        estudiante_id=current_user.id
    ).all()

    return render_template(
        'estudiante/dashboard.html',
        matriculas=matriculas
    )


@estudiante.route('/curso/<int:curso_id>/modulos')
@login_required
def modulos(curso_id):

    modulos = Modulo.query.filter_by(
        curso_id=curso_id
    ).order_by(
        Modulo.orden.asc()
    ).all()

    return render_template(
        'estudiante/modulos.html',
        modulos=modulos
    )


@estudiante.route('/modulo/<int:modulo_id>/materiales')
@login_required
def materiales(modulo_id):

    materiales = Material.query.filter_by(
        modulo_id=modulo_id
    ).order_by(
        Material.fecha_creacion.desc()
    ).all()

    return render_template(
        'estudiante/materiales.html',
        materiales=materiales
    )


@estudiante.route('/modulo/<int:modulo_id>/actividades')
@login_required
def actividades(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    try:
        registrar_ingreso_curso(modulo.curso_id)
    except Exception:
        pass

    actividades = Actividad.query.filter_by(
        modulo_id=modulo_id
    ).order_by(
        Actividad.fecha_creacion.desc()
    ).all()

    ids_actividades = [actividad.id for actividad in actividades]

    entregas = []

    if ids_actividades:
        entregas = EntregaActividad.query.filter(
            EntregaActividad.estudiante_id == current_user.id,
            EntregaActividad.actividad_id.in_(ids_actividades)
        ).all()

    entregas_por_actividad = {}

    for entrega in entregas:
        entregas_por_actividad[entrega.actividad_id] = entrega

    ids_entregas = [entrega.id for entrega in entregas]

    calificaciones = []

    if ids_entregas:
        calificaciones = CalificacionEntrega.query.filter(
            CalificacionEntrega.entrega_id.in_(ids_entregas)
        ).all()

    calificaciones_por_entrega = {}

    for calificacion in calificaciones:
        calificaciones_por_entrega[calificacion.entrega_id] = calificacion

    return render_template(
        'estudiante/actividades.html',
        actividades=actividades,
        entregas_por_actividad=entregas_por_actividad,
        calificaciones_por_entrega=calificaciones_por_entrega
    )


@estudiante.route('/modulo/<int:modulo_id>/examenes')
@login_required
def examenes(modulo_id):

    examenes = Examen.query.filter_by(
        modulo_id=modulo_id
    ).all()

    return render_template(
        'estudiante/examenes.html',
        examenes=examenes
    )


@estudiante.route('/calificaciones')
@login_required
def calificaciones():

    calificaciones = Calificacion.query.filter_by(
        estudiante_id=current_user.id
    ).all()

    return render_template(
        'estudiante/calificaciones.html',
        calificaciones=calificaciones
    )


@estudiante.route('/mensajes')
@login_required
def mensajes():

    mensajes = Mensaje.query.filter_by(
        destinatario_id=current_user.id
    ).order_by(
        Mensaje.fecha_envio.desc()
    ).all()

    return render_template(
        'estudiante/mensajes.html',
        mensajes=mensajes
    )


@estudiante.route('/mensajes/enviar', methods=['GET', 'POST'])
@login_required
def enviar_mensaje():

    usuarios = Usuario.query.filter(
        Usuario.id != current_user.id
    ).order_by(
        Usuario.nombre.asc()
    ).all()

    if request.method == 'POST':

        nuevo_mensaje = Mensaje(
            asunto=request.form.get('asunto'),
            contenido=request.form.get('contenido'),
            remitente_id=current_user.id,
            destinatario_id=request.form.get('destinatario_id')
        )

        db.session.add(nuevo_mensaje)
        db.session.commit()

        return redirect(url_for('estudiante.mensajes'))

    return render_template(
        'estudiante/enviar_mensaje.html',
        usuarios=usuarios
    )


@estudiante.route('/certificados')
@login_required
def certificados():

    certificados = Certificado.query.filter_by(
        estudiante_id=current_user.id
    ).all()

    return render_template(
        'estudiante/certificados.html',
        certificados=certificados
    )

# BLOG ACADEMICO RENOVA

@estudiante.route('/modulo/<int:modulo_id>/blog')
@login_required
def blog_modulo(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    publicaciones = Foro.query.filter_by(
        modulo_id=modulo_id
    ).order_by(
        Foro.fecha_creacion.desc()
    ).all()

    ids_publicaciones = [p.id for p in publicaciones]

    comentarios = []

    if ids_publicaciones:
        comentarios = ComentarioForo.query.filter(
            ComentarioForo.foro_id.in_(ids_publicaciones)
        ).order_by(
            ComentarioForo.fecha_comentario.asc()
        ).all()

    comentarios_por_foro = {}

    for comentario in comentarios:
        comentarios_por_foro.setdefault(comentario.foro_id, []).append(comentario)

    return render_template(
        'estudiante/blog.html',
        modulo=modulo,
        publicaciones=publicaciones,
        comentarios_por_foro=comentarios_por_foro
    )


@estudiante.route('/blog/<int:foro_id>/comentar', methods=['POST'])
@login_required
def comentar_blog(foro_id):

    foro = Foro.query.get_or_404(foro_id)

    texto = request.form.get('comentario', '').strip()

    if texto:

        nuevo_comentario = ComentarioForo(
            comentario=texto,
            foro_id=foro_id,
            usuario_id=current_user.id
        )

        db.session.add(nuevo_comentario)
        db.session.commit()

    return redirect(url_for('estudiante.blog_modulo', modulo_id=foro.modulo_id))


@estudiante.route('/actividad/<int:actividad_id>/entregar', methods=['POST'])
@login_required
def entregar_actividad(actividad_id):

    actividad = Actividad.query.get_or_404(actividad_id)

    enlace = request.form.get('enlace', '').strip()
    comentario = request.form.get('comentario', '').strip()

    entrega = EntregaActividad.query.filter_by(
        estudiante_id=current_user.id,
        actividad_id=actividad_id
    ).first()

    if entrega:
        entrega.enlace = enlace
        entrega.comentario = comentario
        entrega.fecha_entrega = datetime.utcnow()
    else:
        entrega = EntregaActividad(
            estudiante_id=current_user.id,
            actividad_id=actividad_id,
            enlace=enlace,
            comentario=comentario
        )
        db.session.add(entrega)

    db.session.commit()

    return redirect(url_for('estudiante.actividades', modulo_id=actividad.modulo_id))

# ===== EXÁMENES EN LÍNEA ESTUDIANTE RENOVA =====
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session
from database.db import db
from models.curso import Curso
from models.modulo import Modulo
from models.matricula import Matricula
from models.examen import Examen
from models.pregunta_examen import PreguntaExamen
from models.opcion_pregunta import OpcionPregunta
from models.intento_examen import IntentoExamen
from models.respuesta_examen import RespuestaExamen


def _estudiante_id_examenes():
    posibles = [
        'usuario_id',
        'user_id',
        'id_usuario',
        'id',
        'estudiante_id',
        'usuario'
    ]

    for clave in posibles:
        valor = session.get(clave)

        if isinstance(valor, dict):
            for subclave in ['id', 'usuario_id', 'user_id', 'id_usuario']:
                if valor.get(subclave):
                    return valor.get(subclave)

        if valor:
            return valor

    return None



def _estudiante_matriculado_en_examen(examen, estudiante_id):
    modulo = Modulo.query.get(examen.modulo_id)
    if not modulo:
        return False

    matricula = Matricula.query.filter_by(
        estudiante_id=estudiante_id,
        curso_id=modulo.curso_id
    ).first()

    return matricula is not None


def _estado_disponibilidad_examen(examen):
    ahora = datetime.utcnow()

    if not examen.activo:
        return False, "No disponible"

    if examen.fecha_inicio and ahora < examen.fecha_inicio:
        return False, "Aún no está disponible"

    if examen.fecha_fin and ahora > examen.fecha_fin:
        return False, "Fecha vencida"

    return True, "Disponible"


@estudiante.route('/examenes-linea')
def examenes_linea_estudiante():
    estudiante_id = _estudiante_id_examenes()

    if not estudiante_id:
        return redirect('/login')

    matriculas = Matricula.query.filter_by(estudiante_id=estudiante_id).all()
    datos = []

    for matricula in matriculas:
        curso = Curso.query.get(matricula.curso_id)
        if not curso:
            continue

        modulos = Modulo.query.filter_by(curso_id=curso.id).all()

        for modulo in modulos:
            examenes = Examen.query.filter_by(modulo_id=modulo.id, activo=True).order_by(Examen.id.desc()).all()

            for examen in examenes:
                intento = IntentoExamen.query.filter_by(
                    examen_id=examen.id,
                    estudiante_id=estudiante_id
                ).order_by(IntentoExamen.id.desc()).first()

                disponible, mensaje = _estado_disponibilidad_examen(examen)

                datos.append({
                    "curso": curso,
                    "modulo": modulo,
                    "examen": examen,
                    "intento": intento,
                    "disponible": disponible,
                    "mensaje": mensaje
                })

    return render_template('estudiante/examenes_linea.html', datos=datos)


@estudiante.route('/examenes/<int:examen_id>/presentar', methods=['GET', 'POST'])
def presentar_examen_linea(examen_id):
    estudiante_id = _estudiante_id_examenes()

    if not estudiante_id:
        return redirect('/login')

    examen = Examen.query.get_or_404(examen_id)

    if not _estudiante_matriculado_en_examen(examen, estudiante_id):
        flash("No tiene matrícula activa para presentar este examen.", "danger")
        return redirect('/estudiante/examenes-linea')

    disponible, mensaje = _estado_disponibilidad_examen(examen)
    if not disponible:
        flash(mensaje, "warning")
        return redirect('/estudiante/examenes-linea')

    intento_anterior = IntentoExamen.query.filter_by(
        examen_id=examen.id,
        estudiante_id=estudiante_id
    ).order_by(IntentoExamen.id.desc()).first()

    if intento_anterior:
        flash("Este examen ya fue presentado.", "info")
        return redirect(url_for('estudiante.resultado_examen_linea', intento_id=intento_anterior.id))

    preguntas = PreguntaExamen.query.filter_by(
        examen_id=examen.id,
        activo=True
    ).order_by(PreguntaExamen.orden.asc(), PreguntaExamen.id.asc()).all()

    if not preguntas:
        flash("Este examen todavía no tiene preguntas.", "warning")
        return redirect('/estudiante/examenes-linea')

    opciones_por_pregunta = {}
    for pregunta in preguntas:
        opciones_por_pregunta[pregunta.id] = OpcionPregunta.query.filter_by(
            pregunta_id=pregunta.id
        ).order_by(OpcionPregunta.orden.asc()).all()

    if request.method == 'POST':
        for pregunta in preguntas:
            if not request.form.get(f'pregunta_{pregunta.id}'):
                flash("Debe responder todas las preguntas antes de enviar.", "warning")
                return redirect(url_for('estudiante.presentar_examen_linea', examen_id=examen.id))

        intento = IntentoExamen(
            examen_id=examen.id,
            estudiante_id=estudiante_id,
            fecha_inicio=datetime.utcnow(),
            fecha_fin=datetime.utcnow(),
            estado='Finalizado',
            ip=request.remote_addr
        )

        db.session.add(intento)
        db.session.flush()

        puntaje_total = 0
        puntaje_obtenido = 0

        for pregunta in preguntas:
            puntaje_total += pregunta.puntos or 0

            opcion_id = int(request.form.get(f'pregunta_{pregunta.id}'))
            opcion = OpcionPregunta.query.filter_by(
                id=opcion_id,
                pregunta_id=pregunta.id
            ).first()

            es_correcta = bool(opcion and opcion.correcta)
            puntos = pregunta.puntos if es_correcta else 0
            puntaje_obtenido += puntos

            respuesta = RespuestaExamen(
                intento_id=intento.id,
                pregunta_id=pregunta.id,
                opcion_id=opcion.id if opcion else None,
                respuesta_texto=opcion.texto if opcion else '',
                es_correcta=es_correcta,
                puntos_obtenidos=puntos
            )

            db.session.add(respuesta)

        nota = round((puntaje_obtenido / puntaje_total) * 5, 2) if puntaje_total > 0 else 0

        intento.puntaje_total = puntaje_total
        intento.puntaje_obtenido = puntaje_obtenido
        intento.nota = nota

        db.session.commit()

        flash("Examen enviado correctamente.", "success")
        return redirect(url_for('estudiante.resultado_examen_linea', intento_id=intento.id))

    return render_template(
        'estudiante/presentar_examen.html',
        examen=examen,
        preguntas=preguntas,
        opciones_por_pregunta=opciones_por_pregunta
    )


@estudiante.route('/examenes/resultado/<int:intento_id>')
def resultado_examen_linea(intento_id):
    estudiante_id = _estudiante_id_examenes()

    if not estudiante_id:
        return redirect('/login')

    intento = IntentoExamen.query.get_or_404(intento_id)

    if str(intento.estudiante_id) != str(estudiante_id):
        flash("No tiene permiso para ver este resultado.", "danger")
        return redirect('/estudiante/examenes-linea')

    examen = Examen.query.get_or_404(intento.examen_id)
    respuestas = RespuestaExamen.query.filter_by(intento_id=intento.id).all()

    preguntas = {}
    opciones = {}
    correctas = {}

    for respuesta in respuestas:
        pregunta = PreguntaExamen.query.get(respuesta.pregunta_id)
        preguntas[respuesta.pregunta_id] = pregunta

        if respuesta.opcion_id:
            opciones[respuesta.opcion_id] = OpcionPregunta.query.get(respuesta.opcion_id)

        correcta = OpcionPregunta.query.filter_by(
            pregunta_id=respuesta.pregunta_id,
            correcta=True
        ).first()

        correctas[respuesta.pregunta_id] = correcta

    return render_template(
        'estudiante/resultado_examen.html',
        examen=examen,
        intento=intento,
        respuestas=respuestas,
        preguntas=preguntas,
        opciones=opciones,
        correctas=correctas
    )
