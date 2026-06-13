from database.db import db


class Pregunta(db.Model):

    __tablename__ = 'preguntas'

    id = db.Column(db.Integer, primary_key=True)

    enunciado = db.Column(db.Text, nullable=False)

    opcion_a = db.Column(db.String(255), nullable=False)

    opcion_b = db.Column(db.String(255), nullable=False)

    opcion_c = db.Column(db.String(255), nullable=False)

    opcion_d = db.Column(db.String(255), nullable=False)

    respuesta_correcta = db.Column(db.String(1), nullable=False)

    puntaje = db.Column(db.Float, default=1)

    examen_id = db.Column(
        db.Integer,
        db.ForeignKey('examenes.id'),
        nullable=False
    )