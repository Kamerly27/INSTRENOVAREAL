from datetime import datetime
from database.db import db


class CalificacionEntrega(db.Model):
    __tablename__ = 'calificaciones_entrega'

    id = db.Column(db.Integer, primary_key=True)
    entrega_id = db.Column(db.Integer, nullable=False, unique=True)
    nota = db.Column(db.Float, nullable=True)
    retroalimentacion = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(50), default='Pendiente')
    fecha_calificacion = db.Column(db.DateTime, nullable=True)
