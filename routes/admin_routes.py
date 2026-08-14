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
from models.pregunta_examen import PreguntaExamen
from models.opcion_pregunta import OpcionPregunta
from models.intento_examen import IntentoExamen
from models.respuesta_examen import RespuestaExamen



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
    estudiante = Usuario.query.get(certificado.estudiante_id)
    curso = Curso.query.get(certificado.curso_id)

    try:
        registrar_certificado_en_verificacion(certificado)
    except Exception as error:
        print("No se pudo registrar en verificación al descargar:", error)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    verde = colors.HexColor("#064A33")
    verde_claro = colors.HexColor("#E9FFF4")
    dorado = colors.HexColor("#C79A22")
    gris_fondo = colors.HexColor("#EEF3F7")
    gris_borde = colors.HexColor("#DDE3EA")
    texto = colors.HexColor("#111827")
    gris_texto = colors.HexColor("#607086")

    codigo = certificado.codigo_verificacion
    base_verificacion = os.environ.get("VERIFICATION_BASE_URL", "https://verificacio-renova.onrender.com").rstrip("/")
    url_verificacion = f"{base_verificacion}/verificar/{codigo}"

    nombre_estudiante = f"{estudiante.nombre} {estudiante.apellido}".upper() if estudiante else "ESTUDIANTE"
    nombre_curso = curso.nombre.upper() if curso else "PROGRAMA ACADÉMICO"

    tipo_doc = getattr(estudiante, "tipo_documento", "") or "CC"
    numero_doc = getattr(estudiante, "numero_documento", "") or ""
    documento = f"{tipo_doc}: {numero_doc}".strip()

    fecha = certificado.fecha_emision.strftime("%d/%m/%Y") if certificado.fecha_emision else ""

    def texto_ajustado_centro(valor, x, y, ancho, fuente, tamano, minimo=9):
        valor = str(valor)
        actual = tamano
        while c.stringWidth(valor, fuente, actual) > ancho and actual > minimo:
            actual -= 1
        c.setFont(fuente, actual)
        c.drawCentredString(x, y, valor)

    # Fondo
    c.setFillColor(gris_fondo)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Tarjeta principal
    margen = 32
    c.setFillColor(colors.white)
    c.roundRect(margen, margen, width - 2*margen, height - 2*margen, 18, fill=1, stroke=0)

    # Encabezado verde
    header_y = height - 122
    c.setFillColor(verde)
    c.roundRect(margen, header_y, width - 2*margen, 92, 16, fill=1, stroke=0)

    # Logo
    logo_dibujado = False
    rutas_logo = [
        os.path.join("static", "img", "logo.png"),
        os.path.join("static", "images", "logo.png"),
        os.path.join("static", "logo.png"),
        os.path.join("static", "assets", "logo.png"),
    ]

    for ruta_logo in rutas_logo:
        if os.path.exists(ruta_logo):
            try:
                c.drawImage(ruta_logo, margen + 28, header_y + 20, width=55, height=55, preserveAspectRatio=True, mask="auto")
                logo_dibujado = True
                break
            except Exception:
                pass

    if not logo_dibujado:
        c.setFillColor(colors.white)
        c.circle(margen + 55, header_y + 47, 26, fill=1, stroke=0)
        c.setFillColor(verde)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(margen + 55, header_y + 43, "RENOVA")

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(margen + 150, header_y + 52, "INSTITUTO RENOVA")
    c.setFont("Helvetica", 13)
    c.drawString(margen + 150, header_y + 30, "Sistema académico institucional de certificación")

    c.setFillColor(colors.HexColor("#D9FBE6"))
    c.roundRect(width - 205, header_y + 28, 145, 36, 18, fill=1, stroke=0)
    c.setFillColor(verde)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width - 132, header_y + 42, "CERTIFICADO VÁLIDO")

    # Línea dorada
    c.setFillColor(dorado)
    c.rect(margen + 25, header_y - 7, width - 2*margen - 50, 4, fill=1, stroke=0)

    # Título
    c.setFillColor(verde)
    c.setFont("Helvetica-Bold", 31)
    c.drawCentredString(width / 2, 416, "CERTIFICADO ACADÉMICO")

    c.setFillColor(dorado)
    c.rect(width/2 - 145, 399, 290, 2, fill=1, stroke=0)

    c.setFillColor(texto)
    c.setFont("Helvetica", 15)
    c.drawCentredString(width / 2, 363, "El Instituto Renova certifica que:")

    # Nombre
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(gris_borde)
    c.setLineWidth(1.2)
    c.roundRect(105, 310, width - 210, 48, 10, fill=1, stroke=1)

    c.setFillColor(texto)
    texto_ajustado_centro(nombre_estudiante, width / 2, 329, width - 250, "Helvetica-Bold", 22, 13)

    c.setFillColor(gris_texto)
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, 288, documento)

    c.setFillColor(texto)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, 252, "cursó y aprobó satisfactoriamente el programa académico:")

    # Programa separado del QR
    c.setFillColor(verde_claro)
    c.setStrokeColor(colors.HexColor("#72E39B"))
    c.setLineWidth(1.2)
    c.roundRect(70, 190, 545, 52, 12, fill=1, stroke=1)

    c.setFillColor(verde)
    texto_ajustado_centro(nombre_curso, 342, 210, 505, "Helvetica-Bold", 18, 10)

    c.setFillColor(texto)
    c.setFont("Helvetica", 10)
    c.drawCentredString(342, 165, "Certificado otorgado por el Instituto Renova como constancia académica institucional.")

    # Cajas inferiores
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(gris_borde)
    c.roundRect(70, 105, 205, 50, 9, fill=1, stroke=1)

    c.setFillColor(verde)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(84, 138, "FECHA DE EXPEDICIÓN")
    c.setFillColor(texto)
    c.setFont("Helvetica", 10)
    c.drawString(84, 119, fecha)

    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(gris_borde)
    c.roundRect(295, 105, 300, 50, 9, fill=1, stroke=1)

    c.setFillColor(verde)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(309, 138, "CÓDIGO DE VERIFICACIÓN")
    c.setFillColor(texto)
    c.setFont("Helvetica", 10)
    c.drawString(309, 119, codigo)

    # QR en panel independiente
    qr_x = 650
    qr_y = 90
    qr_w = 135
    qr_h = 165

    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(gris_borde)
    c.roundRect(qr_x, qr_y, qr_w, qr_h, 10, fill=1, stroke=1)

    c.setFillColor(verde)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(qr_x + qr_w/2, qr_y + qr_h - 25, "VERIFICACIÓN EN LÍNEA")

    qr_code = qr.QrCodeWidget(url_verificacion)
    bounds = qr_code.getBounds()
    qr_size = 72
    drawing = Drawing(
        qr_size,
        qr_size,
        transform=[
            qr_size / (bounds[2] - bounds[0]),
            0,
            0,
            qr_size / (bounds[3] - bounds[1]),
            0,
            0
        ]
    )
    drawing.add(qr_code)
    renderPDF.draw(drawing, c, qr_x + 31, qr_y + 55)

    c.setFillColor(gris_texto)
    c.setFont("Helvetica", 7)
    c.drawCentredString(qr_x + qr_w/2, qr_y + 22, "Escanee para verificar")

    # Enlace
    c.setFillColor(colors.HexColor("#2563EB"))
    c.setFont("Helvetica", 7)
    c.drawCentredString(342, 76, url_verificacion)
    c.linkURL(url_verificacion, (150, 68, 535, 85), relative=0)

    c.setFillColor(gris_texto)
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, 52, "Este certificado puede ser validado únicamente mediante el sistema oficial de verificación del Instituto Renova.")

    c.showPage()
    c.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"certificado_{codigo}.pdf",
        mimetype="application/pdf"
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


@admin.route('/sincronizar-certificados-verificacion')
def sincronizar_certificados_verificacion():

    certificados = Certificado.query.order_by(Certificado.id.desc()).all()

    total = 0
    enviados = 0
    errores = 0

    for certificado in certificados:
        total += 1

        try:
            registrado = registrar_certificado_en_verificacion(certificado)

            if registrado:
                enviados += 1
            else:
                errores += 1

        except Exception as error:
            print("Error sincronizando certificado:", error)
            errores += 1

    return f"""
    <h2>Sincronización de certificados</h2>
    <p>Total certificados en campus: {total}</p>
    <p>Enviados correctamente a verificación: {enviados}</p>
    <p>Con error: {errores}</p>
    <br>
    <a href='/admin/certificados'>Volver a certificados</a>
    """


@admin.route('/sincronizar-certificados-ahora')
def sincronizar_certificados_ahora():

    certificados = Certificado.query.order_by(Certificado.id.desc()).all()

    total = 0
    enviados = 0
    errores = 0

    for certificado in certificados:
        total += 1

        try:
            registrado = registrar_certificado_en_verificacion(certificado)

            if registrado:
                enviados += 1
            else:
                errores += 1

        except Exception as error:
            print("Error sincronizando certificado:", error)
            errores += 1

    return f"""
    <h2>Sincronización de certificados</h2>
    <p>Total certificados en campus: {total}</p>
    <p>Enviados correctamente a verificación: {enviados}</p>
    <p>Con error: {errores}</p>
    <br>
    <a href='/admin/certificados'>Volver a certificados</a>
    """
