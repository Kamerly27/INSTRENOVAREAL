from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from werkzeug.security import generate_password_hash
from io import BytesIO
import uuid
import os

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from database.db import db
from models.usuario import Usuario
from models.curso import Curso
from models.matricula import Matricula
from models.certificado import Certificado
from models.mensaje import Mensaje

from models.modulo import Modulo
from models.material import Material
from models.actividad import Actividad
from models.examen import Examen
from models.calificacion import Calificacion
from models.foro import Foro
from models.comentario_foro import ComentarioForo
from models.ingreso_curso import IngresoCurso
from models.entrega_actividad import EntregaActividad


admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html')


@admin.route('/usuarios')
def usuarios():
    usuarios = Usuario.query.order_by(Usuario.fecha_registro.desc()).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@admin.route('/usuarios/crear', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        existe = Usuario.query.filter_by(correo=request.form.get('correo')).first()

        if existe:
            flash('Ya existe un usuario con ese correo.')
            return redirect(url_for('admin.crear_usuario'))

        nuevo_usuario = Usuario(
            nombre=request.form.get('nombre'),
            apellido=request.form.get('apellido'),
            tipo_documento=request.form.get('tipo_documento'),
            numero_documento=request.form.get('numero_documento'),
            correo=request.form.get('correo'),
            password=generate_password_hash(request.form.get('password')),
            rol=request.form.get('rol'),
            activo=True
        )

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            return redirect(url_for('admin.usuarios'))

        except IntegrityError:
            db.session.rollback()
            flash('No se pudo crear el usuario. Revise si el correo o documento ya existe.')
            return redirect(url_for('admin.crear_usuario'))

    return render_template('admin/crear_usuario.html')


@admin.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        usuario.nombre = request.form.get('nombre')
        usuario.apellido = request.form.get('apellido')
        usuario.tipo_documento = request.form.get('tipo_documento')
        usuario.numero_documento = request.form.get('numero_documento')
        usuario.correo = request.form.get('correo')
        usuario.rol = request.form.get('rol')
        usuario.activo = True if request.form.get('activo') == '1' else False

        try:
            db.session.commit()
            return redirect(url_for('admin.usuarios'))

        except IntegrityError:
            db.session.rollback()
            flash('No se pudo editar el usuario. Revise si el correo o documento ya existe.')
            return redirect(url_for('admin.editar_usuario', id=id))

    return render_template('admin/editar_usuario.html', usuario=usuario)


@admin.route('/usuarios/eliminar/<int:id>')
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    cursos_docente = Curso.query.filter_by(docente_id=usuario.id).all()

    if cursos_docente:
        usuario.activo = False
        db.session.commit()
        flash('El docente tiene cursos asignados. Por seguridad no se borró; quedó desactivado.')
        return redirect(url_for('admin.usuarios'))

    try:
        Mensaje.query.filter(
            or_(
                Mensaje.remitente_id == usuario.id,
                Mensaje.destinatario_id == usuario.id
            )
        ).delete(synchronize_session=False)

        ComentarioForo.query.filter_by(
            usuario_id=usuario.id
        ).delete(synchronize_session=False)

        Calificacion.query.filter_by(
            estudiante_id=usuario.id
        ).delete(synchronize_session=False)

        Certificado.query.filter_by(
            estudiante_id=usuario.id
        ).delete(synchronize_session=False)

        Matricula.query.filter_by(
            estudiante_id=usuario.id
        ).delete(synchronize_session=False)

        IngresoCurso.query.filter_by(
            estudiante_id=usuario.id
        ).delete(synchronize_session=False)

        EntregaActividad.query.filter_by(
            estudiante_id=usuario.id
        ).delete(synchronize_session=False)

        db.session.delete(usuario)
        db.session.commit()

        flash('Usuario eliminado correctamente.')
        return redirect(url_for('admin.usuarios'))

    except IntegrityError:
        db.session.rollback()
        usuario.activo = False
        db.session.commit()
        flash('No se pudo borrar por datos relacionados. El usuario quedó desactivado.')
        return redirect(url_for('admin.usuarios'))


@admin.route('/cursos')
def cursos():
    cursos = Curso.query.order_by(Curso.id.desc()).all()
    return render_template('admin/cursos.html', cursos=cursos)


@admin.route('/cursos/crear', methods=['GET', 'POST'])
def crear_curso():
    docentes = Usuario.query.filter_by(rol='docente', activo=True).all()

    if request.method == 'POST':
        nuevo_curso = Curso(
            nombre=request.form.get('nombre'),
            descripcion=request.form.get('descripcion'),
            docente_id=request.form.get('docente_id'),
            activo=True
        )

        db.session.add(nuevo_curso)
        db.session.commit()

        return redirect(url_for('admin.cursos'))

    return render_template('admin/crear_curso.html', docentes=docentes)


@admin.route('/cursos/editar/<int:id>', methods=['GET', 'POST'])
def editar_curso(id):
    curso = Curso.query.get_or_404(id)
    docentes = Usuario.query.filter_by(rol='docente', activo=True).all()

    if request.method == 'POST':
        curso.nombre = request.form.get('nombre')
        curso.descripcion = request.form.get('descripcion')
        curso.docente_id = request.form.get('docente_id')
        curso.activo = True if request.form.get('activo') == '1' else False

        db.session.commit()
        return redirect(url_for('admin.cursos'))

    return render_template('admin/editar_curso.html', curso=curso, docentes=docentes)


@admin.route('/cursos/eliminar/<int:id>')
def eliminar_curso(id):
    curso = Curso.query.get_or_404(id)

    tiene_matriculas = Matricula.query.filter_by(curso_id=curso.id).first()
    tiene_certificados = Certificado.query.filter_by(curso_id=curso.id).first()
    tiene_modulos = Modulo.query.filter_by(curso_id=curso.id).first()

    if tiene_matriculas or tiene_certificados or tiene_modulos:
        curso.activo = False
        db.session.commit()
        flash('El curso tiene información relacionada. Por seguridad no se borró; quedó desactivado.')
        return redirect(url_for('admin.cursos'))

    db.session.delete(curso)
    db.session.commit()

    flash('Curso eliminado correctamente.')
    return redirect(url_for('admin.cursos'))


@admin.route('/matriculas')
def matriculas():
    matriculas = Matricula.query.order_by(Matricula.fecha_matricula.desc()).all()
    return render_template('admin/matriculas.html', matriculas=matriculas)


@admin.route('/matriculas/crear', methods=['GET', 'POST'])
def crear_matricula():
    estudiantes = Usuario.query.filter_by(rol='estudiante', activo=True).all()
    cursos = Curso.query.filter_by(activo=True).all()

    if request.method == 'POST':
        nueva_matricula = Matricula(
            estudiante_id=request.form.get('estudiante_id'),
            curso_id=request.form.get('curso_id'),
            estado='activa'
        )

        try:
            db.session.add(nueva_matricula)
            db.session.commit()
            return redirect(url_for('admin.matriculas'))

        except IntegrityError:
            db.session.rollback()
            flash('No se pudo crear la matrícula. Revise si el estudiante ya está matriculado en ese curso.')
            return redirect(url_for('admin.crear_matricula'))

    return render_template(
        'admin/crear_matricula.html',
        estudiantes=estudiantes,
        cursos=cursos
    )


@admin.route('/certificados')
def certificados():
    certificados = Certificado.query.order_by(Certificado.fecha_emision.desc()).all()
    return render_template('admin/certificados.html', certificados=certificados)


@admin.route('/certificados/generar', methods=['GET', 'POST'])
def generar_certificado():
    estudiantes = Usuario.query.filter_by(rol='estudiante', activo=True).all()
    cursos = Curso.query.filter_by(activo=True).all()

    if request.method == 'POST':
        codigo = f"REN-{uuid.uuid4().hex[:10].upper()}"

        nuevo_certificado = Certificado(
            codigo_verificacion=codigo,
            estudiante_id=request.form.get('estudiante_id'),
            curso_id=request.form.get('curso_id')
        )

        db.session.add(nuevo_certificado)
        db.session.commit()

        return redirect(url_for('admin.certificados'))

    return render_template(
        'admin/generar_certificado.html',
        estudiantes=estudiantes,
        cursos=cursos
    )


@admin.route('/certificados/descargar/<int:id>')
def descargar_certificado(id):
    certificado = Certificado.query.get_or_404(id)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    base_static = os.path.join(os.getcwd(), 'static')
    logo_path = os.path.join(base_static, 'img', 'logo.png')

    pdf.setFillColor(colors.HexColor("#F8FAFC"))
    pdf.rect(0, 0, width, height, fill=True, stroke=False)

    pdf.setStrokeColor(colors.HexColor("#0F172A"))
    pdf.setLineWidth(4)
    pdf.rect(35, 35, width - 70, height - 70, fill=False)

    pdf.setStrokeColor(colors.HexColor("#2563EB"))
    pdf.setLineWidth(2)
    pdf.rect(52, 52, width - 104, height - 104, fill=False)

    if os.path.exists(logo_path):
        pdf.drawImage(
            logo_path,
            width / 2 - 45,
            height - 132,
            width=90,
            height=90,
            preserveAspectRatio=True,
            mask='auto'
        )

    pdf.setFillColor(colors.HexColor("#0F172A"))
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 165, "INSTITUTO RENOVA")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width / 2,
        height - 190,
        "Formación para el Trabajo y el Desarrollo Humano"
    )

    pdf.setFillColor(colors.HexColor("#2563EB"))
    pdf.setFont("Helvetica-Bold", 34)
    pdf.drawCentredString(width / 2, height - 255, "CERTIFICADO ACADÉMICO")

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica", 18)
    pdf.drawCentredString(width / 2, height - 315, "El Instituto Renova certifica que:")

    nombre = f"{certificado.estudiante.nombre} {certificado.estudiante.apellido}".upper()

    pdf.setFont("Helvetica-Bold", 31)
    pdf.drawCentredString(width / 2, height - 370, nombre)

    tipo_documento = certificado.estudiante.tipo_documento or "Documento"
    numero_documento = certificado.estudiante.numero_documento or "________________"

    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(
        width / 2,
        height - 402,
        f"{tipo_documento}: {numero_documento}"
    )

    pdf.setFont("Helvetica", 17)
    pdf.drawCentredString(
        width / 2,
        height - 455,
        "cursó y aprobó satisfactoriamente el programa académico:"
    )

    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(
        width / 2,
        height - 505,
        certificado.curso.nombre.upper()
    )

    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(
        width / 2,
        height - 545,
        "cumpliendo con los requisitos académicos establecidos por la institución."
    )

    fecha = certificado.fecha_emision.strftime('%d/%m/%Y')

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width / 2,
        105,
        f"Fecha de expedición: {fecha}"
    )

    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(
        width / 2,
        75,
        f"Código de verificación: {certificado.codigo_verificacion}"
    )

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"certificado_{certificado.codigo_verificacion}.pdf",
        mimetype='application/pdf'
    )


@admin.route('/mensajes')
def mensajes():
    mensajes = Mensaje.query.order_by(Mensaje.fecha_envio.desc()).all()
    return render_template('admin/mensajes.html', mensajes=mensajes)


@admin.route('/mensajes/enviar', methods=['GET', 'POST'])
def enviar_mensaje():
    usuarios = Usuario.query.filter_by(activo=True).order_by(Usuario.nombre.asc()).all()

    if request.method == 'POST':
        remitente = Usuario.query.filter_by(rol='admin').first()

        nuevo_mensaje = Mensaje(
            asunto=request.form.get('asunto'),
            contenido=request.form.get('contenido'),
            remitente_id=remitente.id,
            destinatario_id=request.form.get('destinatario_id')
        )

        db.session.add(nuevo_mensaje)
        db.session.commit()

        return redirect(url_for('admin.mensajes'))

    return render_template(
        'admin/enviar_mensaje.html',
        usuarios=usuarios
    )