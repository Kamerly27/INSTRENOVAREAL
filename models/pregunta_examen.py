from datetime import datetime
from database.db import db


class PreguntaExamen(db.Model):
    __tablename__ = 'preguntas_examen'

    id = db.Column(db.Integer, primary_key=True)
    examen_id = db.Column(db.Integer, db.ForeignKey('examenes.id'), nullable=False)
    enunciado = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), default='seleccion_unica')
    puntos = db.Column(db.Float, default=1.0)
    orden = db.Column(db.Integer, default=1)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
