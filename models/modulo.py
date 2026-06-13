from database.db import db
from datetime import datetime


class Modulo(db.Model):

    __tablename__ = 'modulos'

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

    orden = db.Column(
        db.Integer,
        default=1
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    curso_id = db.Column(
        db.Integer,
        db.ForeignKey('cursos.id'),
        nullable=False
    )

    def __repr__(self):
        return f'<Modulo {self.titulo}>'