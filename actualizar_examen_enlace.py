from app import app
from database.db import db


with app.app_context():

    conexion = db.engine.connect()

    conexion.execute(
        db.text(
            '''
            ALTER TABLE examenes
            ADD COLUMN enlace VARCHAR(500)
            '''
        )
    )

    conexion.commit()

    print('Campo enlace agregado correctamente a la tabla examenes.')