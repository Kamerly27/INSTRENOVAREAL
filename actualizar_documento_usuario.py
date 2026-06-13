from app import app
from database.db import db


with app.app_context():

    try:
        db.session.execute(
            db.text("""
                ALTER TABLE usuarios
                ADD COLUMN tipo_documento VARCHAR(20);
            """)
        )
        db.session.commit()
        print("Columna tipo_documento agregada.")
    except Exception:
        db.session.rollback()
        print("La columna tipo_documento ya existe o no se pudo agregar.")

    try:
        db.session.execute(
            db.text("""
                ALTER TABLE usuarios
                ADD COLUMN numero_documento VARCHAR(30);
            """)
        )
        db.session.commit()
        print("Columna numero_documento agregada.")
    except Exception:
        db.session.rollback()
        print("La columna numero_documento ya existe o no se pudo agregar.")

    print("Proceso terminado.")