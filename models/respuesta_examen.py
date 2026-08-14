from database.db import db


class RespuestaExamen(db.Model):
    __tablename__ = 'respuestas_examen'

    id = db.Column(db.Integer, primary_key=True)
    intento_id = db.Column(db.Integer, db.ForeignKey('intentos_examen.id'), nullable=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('preguntas_examen.id'), nullable=False)
    opcion_id = db.Column(db.Integer, nullable=True)
    respuesta_texto = db.Column(db.Text, nullable=True)
    es_correcta = db.Column(db.Boolean, default=False)
    puntos_obtenidos = db.Column(db.Float, default=0)
