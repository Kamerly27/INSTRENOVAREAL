from database.db import db


class OpcionPregunta(db.Model):
    __tablename__ = 'opciones_pregunta'

    id = db.Column(db.Integer, primary_key=True)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('preguntas_examen.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    correcta = db.Column(db.Boolean, default=False)
    orden = db.Column(db.Integer, default=1)
