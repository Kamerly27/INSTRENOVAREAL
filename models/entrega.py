from database.db import db
from datetime import datetime


class Entrega(db.Model):

    __tablename__ = 'entregas'

    id = db.Column(db.Integer, primary_key=True)

    archivo_url = db.Column(db.String(255), nullable=False)

    comentario = db.Column(db.Text)

    nota = db.Column(db.Float)

    fecha_entrega = db.Column(db.DateTime, default=datetime.utcnow)

    actividad_id = db.Column(
        db.Integer,
        db.ForeignKey('actividades.id'),
        nullable=False
    )

    estudiante_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )