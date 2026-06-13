from app import app
from database.db import db
from models.usuario import Usuario
from werkzeug.security import generate_password_hash


with app.app_context():

    correo = "direccion@instrenova.com"

    existe = Usuario.query.filter_by(correo=correo).first()

    if existe:

        print("La administradora ya existe.")

    else:

        admin = Usuario(
            nombre="Dirección",
            apellido="Instituto Renova",
            correo="rectoria@instrenova.com",
            password=generate_password_hash("Renova#Campus2026"),
            rol="admin",
            activo=True
        )

        db.session.add(admin)
        db.session.commit()

        print("Administradora creada correctamente.")