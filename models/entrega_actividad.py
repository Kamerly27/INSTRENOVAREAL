from datetime import datetime
from database.db import db


class EntregaActividad(db.Model):
    __tablename__ = 'entregas_actividad'

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, nullable=False)
    actividad_id = db.Column(db.Integer, nullable=False)
    enlace = db.Column(db.Text, nullable=True)
    comentario = db.Column(db.Text, nullable=True)
    fecha_entrega = db.Column(db.DateTime, default=datetime.utcnow)