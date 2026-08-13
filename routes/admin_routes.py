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

        registrar_certificado_en_verificacion(nuevo_certificado)

        flash(f'Certificado generado correctamente. Código: {codigo}')

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

    def texto_centrado(texto, y, fuente, tamano, color, ancho_maximo=None, interlineado=None):
        texto = str(texto or "")
        pdf.setFillColor(colors.HexColor(color))
        pdf.setFont(fuente, tamano)

        if not ancho_maximo:
            pdf.drawCentredString(width / 2, y, texto)
            return y - (interlineado or tamano + 6)

        palabras = texto.split()
        lineas = []
        linea = ""

        for palabra in palabras:
            prueba = (linea + " " + palabra).strip()

            if pdf.stringWidth(prueba, fuente, tamano) <= ancho_maximo:
                linea = prueba
            else:
                if linea:
                    lineas.append(linea)
                linea = palabra

        if linea:
            lineas.append(linea)

        salto = interlineado or tamano + 7

        for linea in lineas:
            pdf.drawCentredString(width / 2, y, linea)
            y -= salto

        return y

    # Fondo
    pdf.setFillColor(colors.HexColor("#F8FAFC"))
    pdf.rect(0, 0, width, height, fill=True, stroke=False)

    # Marcos
    pdf.setStrokeColor(colors.HexColor("#0F172A"))
    pdf.setLineWidth(4)
    pdf.rect(32, 32, width - 64, height - 64, fill=False)

    pdf.setStrokeColor(colors.HexColor("#C9A227"))
    pdf.setLineWidth(2)
    pdf.rect(50, 50, width - 100, height - 100, fill=False)

    pdf.setFillColor(colors.HexColor("#0B3D2E"))
    pdf.rect(50, height - 82, width - 100, 7, fill=True, stroke=False)

    # Logo
    if os.path.exists(logo_path):
        pdf.drawImage(
            logo_path,
            width / 2 - 38,
            height - 128,
            width=76,
            height=76,
            preserveAspectRatio=True,
            mask='auto'
        )

    # Encabezado
    texto_centrado("INSTITUTO RENOVA", height - 158, "Helvetica-Bold", 28, "#0F172A")
    texto_centrado("Formación para el Trabajo y el Desarrollo Humano", height - 184, "Helvetica", 13, "#0F172A")

    texto_centrado("CERTIFICADO ACADÉMICO", height - 240, "Helvetica-Bold", 34, "#2563EB")
    texto_centrado("El Instituto Renova certifica que:", height - 295, "Helvetica", 17, "#111827")

    nombre = f"{certificado.estudiante.nombre} {certificado.estudiante.apellido}".upper()
    texto_centrado(nombre, height - 345, "Helvetica-Bold", 30, "#0F172A", ancho_maximo=720, interlineado=34)

    tipo_documento = certificado.estudiante.tipo_documento or "Documento"
    numero_documento = certificado.estudiante.numero_documento or "________________"
    texto_centrado(f"{tipo_documento}: {numero_documento}", height - 382, "Helvetica", 14, "#111827")

    texto_centrado(
        "cursó y aprobó satisfactoriamente el programa académico:",
        height - 425,
        "Helvetica",
        15,
        "#111827"
    )

    texto_centrado(
        certificado.curso.nombre.upper(),
        height - 465,
        "Helvetica-Bold",
        25,
        "#0B3D2E",
        ancho_maximo=700,
        interlineado=29
    )

    texto_centrado(
        "cumpliendo con los requisitos académicos establecidos por la institución.",
        108,
        "Helvetica",
        12,
        "#111827",
        ancho_maximo=620,
        interlineado=15
    )

    fecha = certificado.fecha_emision.strftime('%d/%m/%Y')

    texto_centrado(f"Fecha de expedición: {fecha}", 87, "Helvetica", 11, "#111827")
    texto_centrado(f"Código de verificación: {codigo}", 68, "Helvetica-Bold", 10, "#0F172A")
    texto_centrado("Verifique la autenticidad de este certificado en línea:", 52, "Helvetica", 9, "#64748B")

    pdf.setFillColor(colors.HexColor("#2563EB"))
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(width / 2, 39, url_verificacion)

    pdf.linkURL(
        url_verificacion,
        (width / 2 - 220, 34, width / 2 + 220, 48),
        relative=0
    )

    # QR
    qr_code = qr.QrCodeWidget(url_verificacion)
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]

    qr_size = 78
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
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(width - 105, 130, "Verificación QR")

    renderPDF.draw(
        drawing,
        pdf,
        width - 144,
        47
    )

    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(width - 105, 36, "Escanee para verificar")

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
