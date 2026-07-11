import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

from database.db import db
from models.usuario import Usuario
from models.curso import Curso
from models.matricula import Matricula
from models.modulo import Modulo
from models.material import Material
from models.actividad import Actividad
from models.examen import Examen
from models.calificacion import Calificacion
from models.mensaje import Mensaje


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

    return render_template(
        'docente/dashboard.html',
        cursos=cursos
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
            carpeta = os.path.join('static', 'uploads', 'materiales')
            os.makedirs(carpeta, exist_ok=True)

            nombre_seguro = secure_filename(archivo_subido.filename)
            extension = os.path.splitext(nombre_seguro)[1].lower()
            nombre_final = f"{uuid.uuid4().hex}{extension}"

            ruta_archivo = os.path.join(carpeta, nombre_final)
            archivo_subido.save(ruta_archivo)

            archivo_guardado = f"uploads/materiales/{nombre_final}"

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

    examenes = Examen.query.filter_by(
        modulo_id=modulo_id
    ).order_by(
        Examen.fecha_creacion.desc()
    ).all()

    return render_template(
        'docente/examenes.html',
        modulo=modulo,
        examenes=examenes
    )


@docente.route('/modulo/<int:modulo_id>/examenes/crear', methods=['GET', 'POST'])
@login_required
def crear_examen(modulo_id):

    modulo = Modulo.query.get_or_404(modulo_id)

    if request.method == 'POST':

        fecha_inicio_texto = request.form.get('fecha_inicio')
        fecha_fin_texto = request.form.get('fecha_fin')

        fecha_inicio = None
        fecha_fin = None

        if fecha_inicio_texto:
            fecha_inicio = datetime.strptime(fecha_inicio_texto, '%Y-%m-%d')

        if fecha_fin_texto:
            fecha_fin = datetime.strptime(fecha_fin_texto, '%Y-%m-%d')

        nuevo_examen = Examen(
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion'),
            enlace=request.form.get('enlace'),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activo=True if request.form.get('activo') == '1' else False,
            modulo_id=modulo_id
        )

        db.session.add(nuevo_examen)
        db.session.commit()

        return redirect(url_for('docente.examenes', modulo_id=modulo_id))

    return render_template(
        'docente/crear_examen.html',
        modulo=modulo
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

    estudiantes = [
        matricula.estudiante
        for matricula in matriculas
    ]

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