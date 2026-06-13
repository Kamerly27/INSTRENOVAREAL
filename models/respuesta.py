from database.db import db
from datetime import datetime


class Respuesta(db.Model):

    __tablename__ = 'respuestas'

    id = db.Column(db.Integer, primary_key=True)

    respuesta = db.Column(db.String(1), nullable=False)

    es_correcta = db.Column(db.Boolean, default=False)

    fecha_respuesta = db.Column(db.DateTime, default=datetime.utcnow)

    estudiante_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    pregunta_id = db.Column(
        db.Integer,
        db.ForeignKey('preguntas.id'),
        nullable=False
    )