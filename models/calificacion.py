from database.db import db
from datetime import datetime


class Calificacion(db.Model):

    __tablename__ = 'calificaciones'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nota = db.Column(
        db.Float,
        nullable=False
    )

    observacion = db.Column(
        db.Text
    )

    fecha_calificacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    estudiante_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    examen_id = db.Column(
        db.Integer,
        db.ForeignKey('examenes.id'),
        nullable=False
    )

    estudiante = db.relationship(
        'Usuario',
        foreign_keys=[estudiante_id]
    )

    examen = db.relationship(
        'Examen',
        foreign_keys=[examen_id]
    )

    def __repr__(self):
        return f'<Calificacion {self.nota}>'