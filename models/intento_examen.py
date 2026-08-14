from datetime import datetime
from database.db import db


class IntentoExamen(db.Model):
    __tablename__ = 'intentos_examen'

    id = db.Column(db.Integer, primary_key=True)
    examen_id = db.Column(db.Integer, db.ForeignKey('examenes.id'), nullable=False)
    estudiante_id = db.Column(db.Integer, nullable=False)
    fecha_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_fin = db.Column(db.DateTime)
    puntaje_obtenido = db.Column(db.Float, default=0)
    puntaje_total = db.Column(db.Float, default=0)
    nota = db.Column(db.Float, default=0)
    estado = db.Column(db.String(50), default='Finalizado')
    ip = db.Column(db.String(100))
