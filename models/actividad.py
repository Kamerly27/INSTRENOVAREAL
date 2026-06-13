from database.db import db
from datetime import datetime


class Actividad(db.Model):

    __tablename__ = 'actividades'

    id = db.Column(db.Integer, primary_key=True)

    titulo = db.Column(db.String(200), nullable=False)

    descripcion = db.Column(db.Text, nullable=False)

    archivo_url = db.Column(db.String(255))

    fecha_entrega = db.Column(db.DateTime)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    modulo_id = db.Column(
        db.Integer,
        db.ForeignKey('modulos.id'),
        nullable=False
    )