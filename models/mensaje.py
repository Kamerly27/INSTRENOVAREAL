from database.db import db
from datetime import datetime


class Mensaje(db.Model):

    __tablename__ = 'mensajes'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    asunto = db.Column(
        db.String(200),
        nullable=False
    )

    contenido = db.Column(
        db.Text,
        nullable=False
    )

    fecha_envio = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    remitente_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    destinatario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    remitente = db.relationship(
        'Usuario',
        foreign_keys=[remitente_id]
    )

    destinatario = db.relationship(
        'Usuario',
        foreign_keys=[destinatario_id]
    )

    def __repr__(self):
        return f'<Mensaje {self.id}>'