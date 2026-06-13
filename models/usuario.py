from database.db import db
from flask_login import UserMixin
from datetime import datetime


class Usuario(db.Model, UserMixin):

    __tablename__ = 'usuarios'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    apellido = db.Column(
        db.String(100),
        nullable=False
    )

    tipo_documento = db.Column(
        db.String(20)
    )

    numero_documento = db.Column(
        db.String(30),
        unique=True
    )

    correo = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    rol = db.Column(
        db.String(20),
        nullable=False
    )

    foto = db.Column(
        db.String(255)
    )

    activo = db.Column(
        db.Boolean,
        default=True
    )

    fecha_registro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f'<Usuario {self.correo}>'