from database.db import db
from datetime import datetime


class Matricula(db.Model):

    __tablename__ = 'matriculas'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fecha_matricula = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    estado = db.Column(
        db.String(30),
        default='activa'
    )

    estudiante_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    curso_id = db.Column(
        db.Integer,
        db.ForeignKey('cursos.id'),
        nullable=False
    )

    estudiante = db.relationship(
        'Usuario',
        foreign_keys=[estudiante_id]
    )

    def __repr__(self):
        return f'<Matricula {self.id}>'