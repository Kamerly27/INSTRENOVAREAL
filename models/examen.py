from database.db import db
from datetime import datetime


class Examen(db.Model):

    __tablename__ = 'examenes'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    titulo = db.Column(
        db.String(200),
        nullable=False
    )

    descripcion = db.Column(
        db.Text
    )

    enlace = db.Column(
        db.String(500)
    )

    fecha_inicio = db.Column(
        db.DateTime
    )

    fecha_fin = db.Column(
        db.DateTime
    )

    activo = db.Column(
        db.Boolean,
        default=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    modulo_id = db.Column(
        db.Integer,
        db.ForeignKey('modulos.id'),
        nullable=False
    )

    def __repr__(self):
        return f'<Examen {self.titulo}>'