from app import app
from database.db import db

with app.app_context():

    db.session.execute(
        db.text("""
            ALTER TABLE cursos
            ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP
        """)
    )

    db.session.commit()

    print("Columna fecha_creacion agregada correctamente.")