from database.db import db
from datetime import datetime


class Foro(db.Model):

    __tablename__ = 'foros'

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

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    modulo_id = db.Column(
        db.Integer,
        db.ForeignKey('modulos.id'),
        nullable=False
    )