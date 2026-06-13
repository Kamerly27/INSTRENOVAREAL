from database.db import db
from datetime import datetime


class Curso(db.Model):

    __tablename__ = 'cursos'

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    imagen = db.Column(
        db.String(255)
    )

    activo = db.Column(
        db.Boolean,
        default=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    docente_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id')
    )

    docente = db.relationship(
        'Usuario',
        foreign_keys=[docente_id]
    )

    modulos = db.relationship(
        'Modulo',
        backref='curso',
        lazy=True,
        cascade='all, delete-orphan'
    )

    matriculas = db.relationship(
        'Matricula',
        backref='curso',
        lazy=True,
        cascade='all, delete-orphan'
    )

    certificados = db.relationship(
        'Certificado',
        backref='curso',
        lazy=True
    )

    def __repr__(self):
        return f'<Curso {self.nombre}>'