from app import create_app
from models import db
from sqlalchemy import text
import os

app = create_app()

with app.app_context():
    try:
        # Check if column exists
        with db.engine.connect() as conn:
            # Detect database type
            if 'sqlite' in str(db.engine.url):
                result = conn.execute(text("PRAGMA table_info(invoices)"))
                columns = [row[1] for row in result]

                if 'payment_proof_path' not in columns:
                    print("Adding payment_proof_path column...")
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN payment_proof_path VARCHAR(255)"))
                    conn.commit()
                    print("Column added successfully.")
                else:
                    print("Column payment_proof_path already exists.")

            elif 'postgresql' in str(db.engine.url):
                # Postgres check
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='invoices' AND column_name='payment_proof_path'"))
                if result.rowcount == 0:
                    print("Adding payment_proof_path column...")
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN payment_proof_path VARCHAR(255)"))
                    conn.commit()
                    print("Column added successfully.")
                else:
                    print("Column payment_proof_path already exists.")

    except Exception as e:
        print(f"Migration failed: {e}")
