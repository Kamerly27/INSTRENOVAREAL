from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from werkzeug.security import generate_password_hash
from io import BytesIO
import uuid
import os
import json
import urllib.request
import urllib.error

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

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

VERIFICATION_API_URL = os.environ.get(
    "VERIFICATION_API_URL",
    "https://verificacio-renova.onrender.com/api/certificados/registrar"
)

VERIFICATION_API_TOKEN = os.environ.get(
    "VERIFICATION_API_TOKEN",
    "RENOVA-CERT-2026"
)


def registrar_certificado_en_verificacion(certificado):

    estudiante = Usuario.query.get(certificado.estudiante_id)
    curso = Curso.query.get(certificado.curso_id)

    if not estudiante or not curso:
        return False

    tipo_documento = estudiante.tipo_documento or "Documento"
    numero_documento = estudiante.numero_documento or ""

    documento = f"{tipo_documento} {numero_documento}".strip()

    fecha_grado = certificado.fecha_emision.strftime('%d/%m/%Y')

    datos = {
        "codigo": certificado.codigo_verificacion,
        "nombre_estudiante": f"{estudiante.nombre} {estudiante.apellido}",
        "documento": documento,
        "titulo_obtenido": curso.nombre,
        "fecha_grado": fecha_grado,
        "acta": "No aplica",
        "libro": "No aplica",
        "folio": "No aplica",
        "resolucion": "Certificado generado desde la plataforma académica del Instituto Renova",
        "estado": "Registrado y válido en el archivo académico institucional"
    }

    try:
        req = urllib.request.Request(
            VERIFICATION_API_URL,
            data=json.dumps(datos).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-RENOVA-TOKEN": VERIFICATION_API_TOKEN
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=12) as respuesta:
            respuesta.read()

        return True

    except Exception as error:
        print("No se pudo registrar el certificado en verificación:", error)
        return False



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

        registrado = registrar_certificado_en_verificacion(nuevo_certificado)

        if registrado:
            flash(f'Certificado generado y registrado para verificación. Código: {codigo}')
        else:
            flash(f'Certificado generado. Código: {codigo}. Revise la plataforma de verificación.')

        return redirect(url_for('admin.certificados'))

    return render_template(
        'admin/generar_certificado.html',
        estudiantes=estudiantes,
        cursos=cursos
    )


@admin.route('/certificados/descargar/<int:id>')
def descargar_certificado(id):
    certificado = Certificado.query.get_or_404(id)

    registrar_certificado_en_verificacion(certificado)

    codigo = certificado.codigo_verificacion
    url_verificacion = f"https://verificacio-renova.onrender.com/verificar/{codigo}"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    base_static = os.path.join(os.getcwd(), 'static')
    logo_path = os.path.join(base_static, 'img', 'logo.png')

    # Fondo
    pdf.setFillColor(colors.HexColor("#F8FAFC"))
    pdf.rect(0, 0, width, height, fill=True, stroke=False)

    # Marco exterior
    pdf.setStrokeColor(colors.HexColor("#0F172A"))
    pdf.setLineWidth(4)
    pdf.rect(35, 35, width - 70, height - 70, fill=False)

    # Marco interior dorado
    pdf.setStrokeColor(colors.HexColor("#C9A227"))
    pdf.setLineWidth(2)
    pdf.rect(52, 52, width - 104, height - 104, fill=False)

    # Línea decorativa superior
    pdf.setFillColor(colors.HexColor("#0B3D2E"))
    pdf.rect(52, height - 92, width - 104, 8, fill=True, stroke=False)

    # Logo
    if os.path.exists(logo_path):
        pdf.drawImage(
            logo_path,
            width / 2 - 48,
            height - 155,
            width=96,
            height=96,
            preserveAspectRatio=True,
            mask='auto'
        )

    # Encabezado
    pdf.setFillColor(colors.HexColor("#0F172A"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 185, "INSTITUTO RENOVA")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width / 2,
        height - 207,
        "Formación para el Trabajo y el Desarrollo Humano"
    )

    pdf.setFillColor(colors.HexColor("#0B3D2E"))
    pdf.setFont("Helvetica-Bold", 35)
    pdf.drawCentredString(width / 2, height - 265, "CERTIFICADO ACADÉMICO")

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica", 18)
    pdf.drawCentredString(width / 2, height - 318, "El Instituto Renova certifica que:")

    nombre = f"{certificado.estudiante.nombre} {certificado.estudiante.apellido}".upper()

    pdf.setFillColor(colors.HexColor("#0F172A"))
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
        height - 452,
        "cursó y aprobó satisfactoriamente el programa académico:"
    )

    pdf.setFillColor(colors.HexColor("#0B3D2E"))
    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(
        width / 2,
        height - 500,
        certificado.curso.nombre.upper()
    )

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width / 2,
        height - 536,
        "cumpliendo con los requisitos académicos establecidos por la institución."
    )

    fecha = certificado.fecha_emision.strftime('%d/%m/%Y')

    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(
        width / 2,
        142,
        f"Fecha de expedición: {fecha}"
    )

    # Código y enlace
    pdf.setFillColor(colors.HexColor("#0F172A"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(
        width / 2,
        112,
        f"Código de verificación: {codigo}"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        width / 2,
        91,
        "Verifique la autenticidad de este certificado en:"
    )

    pdf.setFillColor(colors.HexColor("#2563EB"))
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        width / 2,
        74,
        url_verificacion
    )

    pdf.linkURL(
        url_verificacion,
        (width / 2 - 230, 66, width / 2 + 230, 84),
        relative=0
    )

    # QR
    qr_code = qr.QrCodeWidget(url_verificacion)
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]

    qr_size = 82
    drawing = Drawing(
        qr_size,
        qr_size,
        transform=[
            qr_size / qr_width,
            0,
            0,
            qr_size / qr_height,
            0,
            0
        ]
    )

    drawing.add(qr_code)

    pdf.setFillColor(colors.HexColor("#0F172A"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(width - 108, 160, "Verificación QR")

    renderPDF.draw(
        drawing,
        pdf,
        width - 150,
        72
    )

    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.drawCentredString(width - 108, 58, "Escanee para verificar")

    # Nota inferior
    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(
        width / 2,
        45,
        "Este certificado puede ser validado únicamente mediante el sistema oficial de verificación del Instituto Renova."
    )

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"certificado_{codigo}.pdf",
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

@admin.route('/crear-tablas-seguimiento')
def crear_tablas_seguimiento():
    db.create_all()
    return 'TABLAS CREADAS CORRECTAMENTE'
