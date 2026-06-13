from database.db import db
from datetime import datetime


class ComentarioForo(db.Model):

    __tablename__ = 'comentarios_foro'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    comentario = db.Column(
        db.Text,
        nullable=False
    )

    fecha_comentario = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    foro_id = db.Column(
        db.Integer,
        db.ForeignKey('foros.id'),
        nullable=False
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )