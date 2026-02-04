import sys
import os
import sqlite3
from sqlalchemy import text, inspect

# Add root to path
sys.path.insert(0, os.getcwd())

from init_db import create_app, check_and_update_schema, db
from models import User

def test_migration_scenario():
    print("=== Testing Migration Robustness ===")
    app = create_app()

    with app.app_context():
        # 1. Verify User table exists and has first_name
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'first_name' not in columns:
            print("ERROR: first_name column missing initially!")
            sys.exit(1)
        print("Initial state: 'first_name' column exists.")

        # 2. Simulate dropped column (old schema version)
        # SQLite doesn't support DROP COLUMN directly in older versions, but current python sqlite3 usually supports it if recent enough.
        # Alternatively, we can rename table, create new without column, etc.
        # But let's try ALTER TABLE DROP COLUMN first.
        print("Simulating old schema (dropping 'first_name')...")
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE users DROP COLUMN first_name"))
                conn.commit()
        except Exception as e:
            print(f"Could not drop column (might be SQLite limitation): {e}")
            # If we can't drop, we can't test this easily on SQLite without rebuilding table.
            # But let's try to add a NEW column to the model instead.
            pass

        # 2b. Alternative test: Add a dummy column to the Model and see if it gets created.
        # But I can't easily modify the Model class at runtime for SQLAlchemy to pick it up in `check_and_update_schema`
        # because it iterates over `model.__table__.columns`.

        # So sticking to "Drop Column" is better if possible.
        # If SQLite fails to drop, verify if it was dropped.
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'first_name' in columns:
            print("Skipping DROP COLUMN test because SQLite didn't support it or failed.")
            # Let's try to Drop the whole table? No, we want to test column migration.

            # Let's try to add a fake column to the DB manually, then see if init_db REMOVES it?
            # No, init_db only ADDS missing columns.

            # Okay, let's try to rename the column in DB, so it looks "missing".
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users RENAME COLUMN first_name TO first_name_old"))
                    conn.commit()
                print("Renamed 'first_name' to 'first_name_old'.")
            except Exception as e:
                print(f"Could not rename column: {e}")
                sys.exit(1)

        # 3. Run Migration
        print("Running check_and_update_schema()...")
        check_and_update_schema(app)

        # 4. Verify Restoration
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('users')]

        if 'first_name' in columns:
            print("SUCCESS: 'first_name' column was restored/added!")
        else:
            print("FAILURE: 'first_name' column is still missing!")
            sys.exit(1)

        # Cleanup (optional, but good for local dev)
        # We might have duplicates if we ran it multiple times?
        # logic says: if not in existing_columns, add it.

        print("Migration Robustness Test Passed.")

if __name__ == "__main__":
    test_migration_scenario()
