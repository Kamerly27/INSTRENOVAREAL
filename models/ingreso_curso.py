from datetime import datetime
from database.db import db


class IngresoCurso(db.Model):
    __tablename__ = 'ingresos_curso'

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, nullable=False)
    curso_id = db.Column(db.Integer, nullable=False)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)