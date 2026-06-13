from database.db import db
from datetime import datetime


class Certificado(db.Model):

    __tablename__ = 'certificados'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    codigo_verificacion = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    fecha_emision = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    pdf_url = db.Column(
        db.String(255)
    )

    estudiante_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    curso_id = db.Column(
        db.Integer,
        db.ForeignKey('cursos.id'),
        nullable=False
    )

    estudiante = db.relationship(
        'Usuario',
        foreign_keys=[estudiante_id]
    )

    def __repr__(self):
        return f'<Certificado {self.codigo_verificacion}>'