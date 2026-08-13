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
