from database.db import db
from datetime import datetime


class Material(db.Model):

    __tablename__ = 'materiales'

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

    archivo = db.Column(
        db.String(255)
    )

    enlace = db.Column(
        db.String(500)
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
        return f'<Material {self.titulo}>'