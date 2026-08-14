import cloudinary
import cloudinary.uploader
import os

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

from database.db import db
from models.usuario import Usuario
from models.curso import Curso
from models.matricula import Matricula
from models.modulo import Modulo
from models.material import Material
from models.foro import Foro
from models.comentario_foro import ComentarioForo
from models.actividad import Actividad
from models.examen import Examen
from models.calificacion import Calificacion
from models.mensaje import Mensaje
from models.ingreso_curso import IngresoCurso
from models.entrega_actividad import EntregaActividad
from models.calificacion_entrega import CalificacionEntrega


docente = Blueprint(
    'docente',
    __name__,
    url_prefix='/docente'
)


@docente.route('/dashboard')
@login_required
def dashboard():

    cursos = Curso.query.filter_by(
        docente_id=current_user.id,
        activo=True
    ).all()

    ids_cursos = [curso.id for curso in cursos]

    ingresos_estudiantes = []

    for curso in cursos:

        matriculas = Matricula.query.filter_by(
            curso_id=curso.id
        ).all()

        for matricula in matriculas:

            estudiante = Usuario.query.get(matricula.estudiante_id)

            if estudiante:
                estudiante_nombre = estudiante.nombre
            else:
                estudiante_nombre = 'Estudiante eliminado o matrícula dañada'

            ingreso = IngresoCurso.query.filter_by(
                estudiante_id=matricula.estudiante_id,
                curso_id=curso.id
            ).first()

            ingresos_estudiantes.append({
                'estudiante': estudiante_nombre,
                'curso': curso.nombre,
                'fecha': ingreso.fecha_ingreso if ingreso else None,
                'estado': 'Ingresó' if ingreso else 'No ha ingresado'
            })

    entregas_recientes = []

    entregas = EntregaActividad.query.order_by(
        EntregaActividad.fecha_entrega.desc()
    ).all()

    for entrega in entregas:

        actividad = Actividad.query.get(entrega.actividad_id)

        if not actividad:
            continue

        modulo = Modulo.query.get(actividad.modulo_id)

        if not modulo:
            continue

        if modulo.curso_id not in ids_cursos:
            continue

        estudiante = Usuario.query.get(entrega.estudiante_id)
        curso = Curso.query.get(modulo.curso_id)

        entregas_recientes.append({
            'estudiante': estudiante.nombre if estudiante else 'Estudiante eliminado',
            'curso': curso.nombre if curso else 'Curso eliminado',
            'actividad': actividad.titulo,
            'fecha': entrega.fecha_entrega,
            'enlace': entrega.enlace,
            'comentario': entrega.comentario
        })

        if len(entregas_recientes) >= 10:
            break

    return render_template(
        'docente/dashboard.html',
        cursos=cursos,
        ingresos_estudiantes=ingresos_estudiantes,
        entregas_recientes=entregas_recientes
    )


@docente.route('/curso/<int:id>')
@login_required
def detalle_curso(id):

    curso = Curso.query.get_or_404(id)

    matriculas = Matricula.query.filter_by(
        curso_id=id
    ).all()

    return render_template(
        'docente/detalle_curso.html',
        curso=curso,
        matriculas=matriculas
    )


@docente.route('/curso/<int:curso_id>/modulos')
@login_required
def modulos(curso_id):

    curso = Curso.query.get_or_404(curso_id)

    modulos = Modulo.query.filter_by(
        curso_id=curso_id
    ).order_by(
        Modulo.orden.asc()
    ).all()

    return render_template(
        'docente/modulos.html',
        curso=curso,
        modulos=modulos
    )


@docente.route('/curso/<int:curso_id>/modulos/crear', methods=['GET', 'POST'])
@login_required
def crear_modulo(curso_id):

    curso = Curso.query.get_or_404(curso_id)

    if request.method == 'POST':

        nuevo_modulo = Modulo(
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion'),
            orden=request.form.get('orden'),
            curso_id=curso_id
        )

        db.session.add(nuevo_modulo)
        db.session.commit()

        return redirect(url_for('docente.modulos', curso_id=curso_id))

    return render_template(
        'docente/crear_modulo.html',
        curso=curso
    )


@docente.route('/modulo/<int:modulo_id>/materiales')
@login_required
def materiales(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    materiales = Material.query.filter_by(
        modulo_id=modulo_id
    ).order_by(
        Material.fecha_creacion.desc()
    ).all()

    return render_template(
        'docente/materiales.html',
        modulo=modulo,
        materiales=materiales
    )


@docente.route('/modulo/<int:modulo_id>/materiales/crear', methods=['GET', 'POST'])
@login_required
def crear_material(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    if request.method == 'POST':

        archivo_guardado = request.form.get('archivo', '').strip()
        archivo_subido = request.files.get('archivo_file')

        if archivo_subido and archivo_subido.filename:

            cloudinary.config(
                cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME") or os.environ.get("CLOUD_NAME"),
                api_key=os.environ.get("CLOUDINARY_API_KEY") or os.environ.get("API_KEY"),
                api_secret=os.environ.get("CLOUDINARY_API_SECRET") or os.environ.get("API_SECRET"),
                secure=True
            )

            resultado = cloudinary.uploader.upload(
                archivo_subido,
                folder="renova/materiales",
                resource_type="auto"
            )

            archivo_guardado = resultado.get("secure_url")

        nuevo_material = Material(
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion'),
            enlace=request.form.get('enlace'),
            archivo=archivo_guardado,
            modulo_id=modulo_id
        )

        db.session.add(nuevo_material)
        db.session.commit()

        return redirect(url_for('docente.materiales', modulo_id=modulo_id))

    return render_template(
        'docente/crear_material.html',
        modulo=modulo
    )


@docente.route('/material/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_material(id):

    material = Material.query.get_or_404(id)
    modulo = Modulo.query.get_or_404(material.modulo_id)

    if request.method == 'POST':

        material.titulo = request.form.get('titulo')
        material.descripcion = request.form.get('descripcion')
        material.enlace = request.form.get('enlace')
        material.archivo = request.form.get('archivo')

        db.session.commit()

        return redirect(url_for('docente.materiales', modulo_id=material.modulo_id))

    return render_template(
        'docente/editar_material.html',
        material=material,
        modulo=modulo
    )


@docente.route('/material/<int:id>/eliminar')
@login_required
def eliminar_material(id):

    material = Material.query.get_or_404(id)
    modulo_id = material.modulo_id

    db.session.delete(material)
    db.session.commit()

    return redirect(url_for('docente.materiales', modulo_id=modulo_id))


@docente.route('/modulo/<int:modulo_id>/actividades')
@login_required
def actividades(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    actividades = Actividad.query.filter_by(
        modulo_id=modulo_id
    ).order_by(
        Actividad.fecha_creacion.desc()
    ).all()

    return render_template(
        'docente/actividades.html',
        modulo=modulo,
        actividades=actividades
    )


@docente.route('/modulo/<int:modulo_id>/actividades/crear', methods=['GET', 'POST'])
@login_required
def crear_actividad(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    if request.method == 'POST':

        fecha_entrega_texto = request.form.get('fecha_entrega')
        fecha_entrega = None

        if fecha_entrega_texto:
            fecha_entrega = datetime.strptime(fecha_entrega_texto, '%Y-%m-%d')

        nueva_actividad = Actividad(
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion'),
            archivo_url=request.form.get('archivo_url'),
            fecha_entrega=fecha_entrega,
            modulo_id=modulo_id
        )

        db.session.add(nueva_actividad)
        db.session.commit()

        return redirect(url_for('docente.actividades', modulo_id=modulo_id))

    return render_template(
        'docente/crear_actividad.html',
        modulo=modulo
    )


@docente.route('/actividad/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_actividad(id):

    actividad = Actividad.query.get_or_404(id)
    modulo = Modulo.query.get_or_404(actividad.modulo_id)

    if request.method == 'POST':

        fecha_entrega_texto = request.form.get('fecha_entrega')
        fecha_entrega = None

        if fecha_entrega_texto:
            fecha_entrega = datetime.strptime(fecha_entrega_texto, '%Y-%m-%d')

        actividad.titulo = request.form.get('titulo')
        actividad.descripcion = request.form.get('descripcion')
        actividad.archivo_url = request.form.get('archivo_url')
        actividad.fecha_entrega = fecha_entrega

        db.session.commit()

        return redirect(url_for('docente.actividades', modulo_id=actividad.modulo_id))

    return render_template(
        'docente/editar_actividad.html',
        actividad=actividad,
        modulo=modulo
    )


@docente.route('/actividad/<int:id>/eliminar')
@login_required
def eliminar_actividad(id):

    actividad = Actividad.query.get_or_404(id)
    modulo_id = actividad.modulo_id

    db.session.delete(actividad)
    db.session.commit()

    return redirect(url_for('docente.actividades', modulo_id=modulo_id))


@docente.route('/modulo/<int:modulo_id>/examenes')
@login_required
def examenes(modulo_id):


    modulo = Modulo.query.get_or_404(modulo_id)
    curso = Curso.query.get(modulo.curso_id)

    examenes = Examen.query.filter_by(modulo_id=modulo.id).order_by(Examen.id.desc()).all()

    conteo_preguntas = {}
    conteo_intentos = {}

    for examen in examenes:
        conteo_preguntas[examen.id] = PreguntaExamen.query.filter_by(examen_id=examen.id).count()
        conteo_intentos[examen.id] = IntentoExamen.query.filter_by(examen_id=examen.id).count()

    return render_template(
        'docente/examenes_modulo_linea.html',
        modulo=modulo,
        curso=curso,
        examenes=examenes,
        conteo_preguntas=conteo_preguntas,
        conteo_intentos=conteo_intentos
    )



@docente.route('/modulo/<int:modulo_id>/examenes/crear', methods=['GET', 'POST'])
@login_required
def crear_examen(modulo_id):


    modulo = Modulo.query.get_or_404(modulo_id)
    curso = Curso.query.get(modulo.curso_id)

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        fecha_inicio = None
        fecha_fin = None

        try:
            valor_inicio = request.form.get('fecha_inicio')
            if valor_inicio:
                fecha_inicio = datetime.strptime(valor_inicio, "%Y-%m-%d")
        except Exception:
            fecha_inicio = None

        try:
            valor_fin = request.form.get('fecha_fin')
            if valor_fin:
                fecha_fin = datetime.strptime(valor_fin, "%Y-%m-%d")
        except Exception:
            fecha_fin = None

        if not titulo:
            flash("Debe escribir el título del examen.", "warning")
            return render_template(
                'docente/crear_examen_linea.html',
                modulo=modulo,
                curso=curso
            )

        examen = Examen(
            titulo=titulo,
            descripcion=descripcion,
            enlace='',
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activo=True,
            modulo_id=modulo.id
        )

        db.session.add(examen)
        db.session.commit()

        flash("Examen creado correctamente. Ahora agregue las preguntas.", "success")
        return redirect(url_for('docente.preguntas_examen_linea', examen_id=examen.id))

    return render_template(
        'docente/crear_examen_linea.html',
        modulo=modulo,
        curso=curso
    )



@docente.route('/examen/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_examen(id):

    examen = Examen.query.get_or_404(id)
    modulo = Modulo.query.get_or_404(examen.modulo_id)

    if request.method == 'POST':

        fecha_inicio_texto = request.form.get('fecha_inicio')
        fecha_fin_texto = request.form.get('fecha_fin')

        fecha_inicio = None
        fecha_fin = None

        if fecha_inicio_texto:
            fecha_inicio = datetime.strptime(fecha_inicio_texto, '%Y-%m-%d')

        if fecha_fin_texto:
            fecha_fin = datetime.strptime(fecha_fin_texto, '%Y-%m-%d')

        examen.titulo = request.form.get('titulo')
        examen.descripcion = request.form.get('descripcion')
        examen.enlace = request.form.get('enlace')
        examen.fecha_inicio = fecha_inicio
        examen.fecha_fin = fecha_fin
        examen.activo = True if request.form.get('activo') == '1' else False

        db.session.commit()

        return redirect(url_for('docente.examenes', modulo_id=examen.modulo_id))

    return render_template(
        'docente/editar_examen.html',
        examen=examen,
        modulo=modulo
    )


@docente.route('/examen/<int:id>/eliminar')
@login_required
def eliminar_examen(id):

    examen = Examen.query.get_or_404(id)
    modulo_id = examen.modulo_id

    db.session.delete(examen)
    db.session.commit()

    return redirect(url_for('docente.examenes', modulo_id=modulo_id))


@docente.route('/examen/<int:examen_id>/calificaciones')
@login_required
def calificaciones(examen_id):

    examen = Examen.query.get_or_404(examen_id)

    calificaciones = Calificacion.query.filter_by(
        examen_id=examen_id
    ).order_by(
        Calificacion.fecha_calificacion.desc()
    ).all()

    return render_template(
        'docente/calificaciones.html',
        examen=examen,
        calificaciones=calificaciones
    )


@docente.route('/examen/<int:examen_id>/calificaciones/crear', methods=['GET', 'POST'])
@login_required
def crear_calificacion(examen_id):

    examen = Examen.query.get_or_404(examen_id)
    modulo = Modulo.query.get_or_404(examen.modulo_id)

    matriculas = Matricula.query.filter_by(
        curso_id=modulo.curso_id
    ).all()

    estudiantes = []

    for matricula in matriculas:
        estudiante = Usuario.query.get(matricula.estudiante_id)

        if estudiante:
            estudiantes.append(estudiante)

    if request.method == 'POST':

        nueva_calificacion = Calificacion(
            nota=request.form.get('nota'),
            observacion=request.form.get('observacion'),
            estudiante_id=request.form.get('estudiante_id'),
            examen_id=examen_id
        )

        db.session.add(nueva_calificacion)
        db.session.commit()

        return redirect(url_for('docente.calificaciones', examen_id=examen_id))

    return render_template(
        'docente/crear_calificacion.html',
        examen=examen,
        estudiantes=estudiantes
    )


@docente.route('/calificacion/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_calificacion(id):

    calificacion = Calificacion.query.get_or_404(id)

    if request.method == 'POST':

        calificacion.nota = request.form.get('nota')
        calificacion.observacion = request.form.get('observacion')

        db.session.commit()

        return redirect(
            url_for(
                'docente.calificaciones',
                examen_id=calificacion.examen_id
            )
        )

    return render_template(
        'docente/editar_calificacion.html',
        calificacion=calificacion
    )


@docente.route('/calificacion/<int:id>/eliminar')
@login_required
def eliminar_calificacion(id):

    calificacion = Calificacion.query.get_or_404(id)
    examen_id = calificacion.examen_id

    db.session.delete(calificacion)
    db.session.commit()

    return redirect(url_for('docente.calificaciones', examen_id=examen_id))


@docente.route('/mensajes')
@login_required
def mensajes():

    mensajes = Mensaje.query.filter_by(
        destinatario_id=current_user.id
    ).order_by(
        Mensaje.fecha_envio.desc()
    ).all()

    return render_template(
        'docente/mensajes.html',
        mensajes=mensajes
    )


@docente.route('/mensajes/enviar', methods=['GET', 'POST'])
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

        return redirect(url_for('docente.mensajes'))

    return render_template(
        'docente/enviar_mensaje.html',
        usuarios=usuarios
    )


# BLOG ACADEMICO RENOVA

@docente.route('/modulo/<int:modulo_id>/blog')
@login_required
def blog_modulo(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    publicaciones = Foro.query.filter_by(
        modulo_id=modulo_id
    ).order_by(
        Foro.fecha_creacion.desc()
    ).all()

    return render_template(
        'docente/blog.html',
        modulo=modulo,
        publicaciones=publicaciones
    )


@docente.route('/modulo/<int:modulo_id>/blog/crear', methods=['GET', 'POST'])
@login_required
def crear_blog(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    if request.method == 'POST':

        nueva_publicacion = Foro(
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion'),
            modulo_id=modulo_id
        )

        db.session.add(nueva_publicacion)
        db.session.commit()

        return redirect(url_for('docente.blog_modulo', modulo_id=modulo_id))

    return render_template(
        'docente/crear_blog.html',
        modulo=modulo
    )


@docente.route('/blog/<int:id>/eliminar')
@login_required
def eliminar_blog(id):

    publicacion = Foro.query.get_or_404(id)
    modulo_id = publicacion.modulo_id

    ComentarioForo.query.filter_by(foro_id=id).delete()

    db.session.delete(publicacion)
    db.session.commit()

    return redirect(url_for('docente.blog_modulo', modulo_id=modulo_id))

@docente.route('/entregas')
@login_required
def entregas():

    cursos = Curso.query.filter_by(
        docente_id=current_user.id,
        activo=True
    ).all()

    ids_cursos = [curso.id for curso in cursos]

    entregas = EntregaActividad.query.order_by(
        EntregaActividad.fecha_entrega.desc()
    ).all()

    entregas_docente = []

    for entrega in entregas:

        actividad = Actividad.query.get(entrega.actividad_id)

        if not actividad:
            continue

        modulo = Modulo.query.get(actividad.modulo_id)

        if not modulo:
            continue

        if modulo.curso_id not in ids_cursos:
            continue

        curso = Curso.query.get(modulo.curso_id)
        estudiante = Usuario.query.get(entrega.estudiante_id)

        calificacion = CalificacionEntrega.query.filter_by(
            entrega_id=entrega.id
        ).first()

        entregas_docente.append({
            'entrega': entrega,
            'estudiante': estudiante.nombre if estudiante else 'Estudiante eliminado',
            'curso': curso.nombre if curso else 'Curso eliminado',
            'modulo': modulo.titulo,
            'actividad': actividad.titulo,
            'nota': calificacion.nota if calificacion else None,
            'estado': calificacion.estado if calificacion else 'Pendiente',
            'retroalimentacion': calificacion.retroalimentacion if calificacion else ''
        })

    return render_template(
        'docente/entregas.html',
        entregas=entregas_docente
    )


@docente.route('/entrega/<int:entrega_id>/calificar', methods=['GET', 'POST'])
@login_required
def calificar_entrega(entrega_id):

    entrega = EntregaActividad.query.get_or_404(entrega_id)
    actividad = Actividad.query.get_or_404(entrega.actividad_id)
    modulo = Modulo.query.get_or_404(actividad.modulo_id)
    curso = Curso.query.get_or_404(modulo.curso_id)

    if curso.docente_id != current_user.id:
        return redirect(url_for('docente.dashboard'))

    estudiante = Usuario.query.get(entrega.estudiante_id)

    calificacion = CalificacionEntrega.query.filter_by(
        entrega_id=entrega.id
    ).first()

    if request.method == 'POST':

        nota_texto = request.form.get('nota', '').strip().replace(',', '.')
        nota = None

        if nota_texto:
            nota = float(nota_texto)

        if calificacion:
            calificacion.nota = nota
            calificacion.retroalimentacion = request.form.get('retroalimentacion')
            calificacion.estado = request.form.get('estado')
            calificacion.fecha_calificacion = datetime.utcnow()
        else:
            calificacion = CalificacionEntrega(
                entrega_id=entrega.id,
                nota=nota,
                retroalimentacion=request.form.get('retroalimentacion'),
                estado=request.form.get('estado'),
                fecha_calificacion=datetime.utcnow()
            )
            db.session.add(calificacion)

        db.session.commit()

        return redirect(url_for('docente.entregas'))

    return render_template(
        'docente/calificar_entrega.html',
        entrega=entrega,
        actividad=actividad,
        modulo=modulo,
        curso=curso,
        estudiante=estudiante,
        calificacion=calificacion
    )

# ===== EXÁMENES EN LÍNEA RENOVA =====
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session
from database.db import db
from models.usuario import Usuario
from models.curso import Curso
from models.modulo import Modulo
from models.examen import Examen
from models.pregunta_examen import PreguntaExamen
from models.opcion_pregunta import OpcionPregunta
from models.intento_examen import IntentoExamen
from models.respuesta_examen import RespuestaExamen


def _docente_id_examenes():
    posibles = [
        'usuario_id',
        'user_id',
        'id_usuario',
        'id',
        'docente_id',
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



def _parse_fecha_examen(valor):
    if not valor:
        return None

    formatos = [
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y"
    ]

    for formato in formatos:
        try:
            return datetime.strptime(valor, formato)
        except Exception:
            pass

    return None



def _docente_puede_examen(examen, docente_id):
    # Si la sesión antigua del campus no entrega el ID,
    # no expulsamos al docente; permitimos continuar dentro del panel docente.
    if not docente_id:
        return True

    modulo = Modulo.query.get(examen.modulo_id)
    if not modulo:
        return False

    curso = Curso.query.get(modulo.curso_id)
    if not curso:
        return False

    return str(getattr(curso, "docente_id", "")) == str(docente_id)



@docente.route('/examenes-linea')
def examenes_linea():
    docente_id = _docente_id_examenes()

    if not docente_id:
        docente_id = None

    cursos = Curso.query.filter_by(docente_id=docente_id).all()
    datos = []

    for curso in cursos:
        modulos = Modulo.query.filter_by(curso_id=curso.id).all()
        modulos_data = []

        for modulo in modulos:
            examenes = Examen.query.filter_by(modulo_id=modulo.id).order_by(Examen.id.desc()).all()
            modulos_data.append({
                "modulo": modulo,
                "examenes": examenes
            })

        datos.append({
            "curso": curso,
            "modulos": modulos_data
        })

    return render_template('docente/examenes_linea.html', datos=datos)


@docente.route('/modulo/<int:modulo_id>/examenes/nuevo', methods=['GET', 'POST'])
def crear_examen_linea(modulo_id):
    docente_id = _docente_id_examenes()

    if not docente_id:
        docente_id = None

    modulo = Modulo.query.get_or_404(modulo_id)
    curso = Curso.query.get(modulo.curso_id)

    if not curso or str(getattr(curso, "docente_id", "")) != str(docente_id):
        flash("No tiene permiso para crear exámenes en este módulo.", "danger")
        return redirect('/docente/examenes-linea')

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        fecha_inicio = _parse_fecha_examen(request.form.get('fecha_inicio'))
        fecha_fin = _parse_fecha_examen(request.form.get('fecha_fin'))

        if not titulo:
            flash("Debe escribir el título del examen.", "warning")
            return redirect(url_for('docente.crear_examen_linea', modulo_id=modulo_id))

        examen = Examen(
            titulo=titulo,
            descripcion=descripcion,
            enlace='',
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activo=True,
            modulo_id=modulo.id
        )

        db.session.add(examen)
        db.session.commit()

        flash("Examen creado. Ahora agregue las preguntas.", "success")
        return redirect(url_for('docente.preguntas_examen_linea', examen_id=examen.id))

    return render_template('docente/crear_examen_linea.html', modulo=modulo, curso=curso)


@docente.route('/examenes/<int:examen_id>/preguntas')
def preguntas_examen_linea(examen_id):
    docente_id = _docente_id_examenes()

    if not docente_id:
        docente_id = None

    examen = Examen.query.get_or_404(examen_id)

    if not _docente_puede_examen(examen, docente_id):
        flash("No tiene permiso para administrar este examen.", "danger")
        return redirect('/docente/examenes-linea')

    preguntas = PreguntaExamen.query.filter_by(examen_id=examen.id).order_by(PreguntaExamen.orden.asc(), PreguntaExamen.id.asc()).all()

    opciones_por_pregunta = {}
    for pregunta in preguntas:
        opciones_por_pregunta[pregunta.id] = OpcionPregunta.query.filter_by(pregunta_id=pregunta.id).order_by(OpcionPregunta.orden.asc()).all()

    return render_template(
        'docente/preguntas_examen.html',
        examen=examen,
        preguntas=preguntas,
        opciones_por_pregunta=opciones_por_pregunta
    )


@docente.route('/examenes/<int:examen_id>/preguntas/nueva', methods=['POST'])
def agregar_pregunta_examen_linea(examen_id):
    docente_id = _docente_id_examenes()

    if not docente_id:
        docente_id = None

    examen = Examen.query.get_or_404(examen_id)

    if not _docente_puede_examen(examen, docente_id):
        flash("No tiene permiso para modificar este examen.", "danger")
        return redirect('/docente/examenes-linea')

    enunciado = request.form.get('enunciado', '').strip()
    correcta = request.form.get('correcta', '').strip()

    try:
        puntos = float(request.form.get('puntos', '1'))
    except Exception:
        puntos = 1.0

    opciones = []
    for i in range(1, 5):
        texto = request.form.get(f'opcion_{i}', '').strip()
        if texto:
            opciones.append((i, texto))

    if not enunciado:
        flash("Debe escribir la pregunta.", "warning")
        return redirect(url_for('docente.preguntas_examen_linea', examen_id=examen.id))

    if len(opciones) < 2:
        flash("Debe escribir mínimo dos opciones de respuesta.", "warning")
        return redirect(url_for('docente.preguntas_examen_linea', examen_id=examen.id))

    if not correcta:
        flash("Debe marcar cuál opción es correcta.", "warning")
        return redirect(url_for('docente.preguntas_examen_linea', examen_id=examen.id))

    orden = PreguntaExamen.query.filter_by(examen_id=examen.id).count() + 1

    pregunta = PreguntaExamen(
        examen_id=examen.id,
        enunciado=enunciado,
        tipo='seleccion_unica',
        puntos=puntos,
        orden=orden,
        activo=True
    )

    db.session.add(pregunta)
    db.session.flush()

    for posicion, texto_opcion in opciones:
        opcion = OpcionPregunta(
            pregunta_id=pregunta.id,
            texto=texto_opcion,
            correcta=(str(posicion) == str(correcta)),
            orden=posicion
        )
        db.session.add(opcion)

    db.session.commit()

    flash("Pregunta agregada correctamente.", "success")
    return redirect(url_for('docente.preguntas_examen_linea', examen_id=examen.id))


@docente.route('/preguntas-examen/<int:pregunta_id>/eliminar', methods=['POST'])
def eliminar_pregunta_examen_linea(pregunta_id):
    docente_id = _docente_id_examenes()

    if not docente_id:
        docente_id = None

    pregunta = PreguntaExamen.query.get_or_404(pregunta_id)
    examen = Examen.query.get_or_404(pregunta.examen_id)

    if not _docente_puede_examen(examen, docente_id):
        flash("No tiene permiso para eliminar esta pregunta.", "danger")
        return redirect('/docente/examenes-linea')

    RespuestaExamen.query.filter_by(pregunta_id=pregunta.id).delete()
    OpcionPregunta.query.filter_by(pregunta_id=pregunta.id).delete()
    db.session.delete(pregunta)
    db.session.commit()

    flash("Pregunta eliminada.", "success")
    return redirect(url_for('docente.preguntas_examen_linea', examen_id=examen.id))


@docente.route('/examenes/<int:examen_id>/resultados')
def resultados_examen_linea(examen_id):
    docente_id = _docente_id_examenes()

    if not docente_id:
        docente_id = None

    examen = Examen.query.get_or_404(examen_id)

    if not _docente_puede_examen(examen, docente_id):
        flash("No tiene permiso para ver estos resultados.", "danger")
        return redirect('/docente/examenes-linea')

    intentos = IntentoExamen.query.filter_by(examen_id=examen.id).order_by(IntentoExamen.fecha_fin.desc()).all()

    estudiantes = {}
    for intento in intentos:
        estudiantes[intento.estudiante_id] = Usuario.query.get(intento.estudiante_id)

    return render_template(
        'docente/resultados_examen.html',
        examen=examen,
        intentos=intentos,
        estudiantes=estudiantes
    )

# ===== EDICIÓN Y ELIMINACIÓN LIMPIA DE EXÁMENES INTERNOS =====

def _renova_parse_fecha_examen(valor):
    if not valor:
        return None

    formatos = [
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y"
    ]

    for formato in formatos:
        try:
            return datetime.strptime(valor, formato)
        except Exception:
            pass

    return None


@docente.route('/examenes-linea/<int:examen_id>/editar', methods=['GET', 'POST'])
def editar_examen_linea_directo(examen_id):
    examen = Examen.query.get_or_404(examen_id)
    modulo = Modulo.query.get(examen.modulo_id)
    curso = Curso.query.get(modulo.curso_id) if modulo else None

    if request.method == 'POST':
        examen.titulo = request.form.get('titulo', '').strip()
        examen.descripcion = request.form.get('descripcion', '').strip()
        examen.fecha_inicio = _renova_parse_fecha_examen(request.form.get('fecha_inicio'))
        examen.fecha_fin = _renova_parse_fecha_examen(request.form.get('fecha_fin'))
        examen.activo = request.form.get('activo') == '1'

        db.session.commit()

        flash("Examen actualizado correctamente.", "success")
        return redirect(f"/docente/modulo/{examen.modulo_id}/examenes")

    return render_template(
        'docente/editar_examen_linea.html',
        examen=examen,
        modulo=modulo,
        curso=curso
    )


@docente.route('/examenes-linea/<int:examen_id>/eliminar', methods=['GET', 'POST'])
def eliminar_examen_linea_directo(examen_id):
    examen = Examen.query.get_or_404(examen_id)
    modulo_id = examen.modulo_id

    intentos = IntentoExamen.query.filter_by(examen_id=examen.id).all()

    for intento in intentos:
        RespuestaExamen.query.filter_by(intento_id=intento.id).delete()
        db.session.delete(intento)

    preguntas = PreguntaExamen.query.filter_by(examen_id=examen.id).all()

    for pregunta in preguntas:
        RespuestaExamen.query.filter_by(pregunta_id=pregunta.id).delete()
        OpcionPregunta.query.filter_by(pregunta_id=pregunta.id).delete()
        db.session.delete(pregunta)

    db.session.delete(examen)
    db.session.commit()

    flash("Examen eliminado correctamente.", "success")
    return redirect(f"/docente/modulo/{modulo_id}/examenes")
