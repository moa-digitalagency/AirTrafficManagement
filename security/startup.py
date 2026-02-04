import os
import sys
import logging
from sqlalchemy import inspect
from models import db, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_production_safety():
    """
    Ensures that the production environment is secure.
    Verifies that the database URL uses PostgreSQL in production.
    """
    node_env = os.environ.get('NODE_ENV', '').lower()

    if node_env == 'production':
        database_url = os.environ.get('DATABASE_URL', '').lower()
        if not (database_url.startswith('postgresql://') or database_url.startswith('postgres://')):
            logger.critical("CRITICAL: Production environment requires PostgreSQL. Startup aborted.")
            sys.exit(1)

def validate_admin_credentials():
    """
    Validates the Super Admin credentials (Anti-Default).
    Checks against a blacklist and enforces minimum length.
    """
    email = os.environ.get('SUPER_ADMIN_EMAIL')
    password = os.environ.get('SUPER_ADMIN_PASSWORD')

    # Only validate if credentials are provided
    if email and password:
        blacklist = ["admin", "123456", "password", "root", "changeMe"]

        if password in blacklist:
            logger.critical("CRITICAL: Super Admin password found in blacklist. Startup aborted.")
            sys.exit(1)

        if len(password) < 12:
            logger.critical("CRITICAL: Super Admin password must be at least 12 characters long. Startup aborted.")
            sys.exit(1)

def seed_super_admin(app):
    """
    Seeds the Super Admin user if it doesn't exist.
    """
    email = os.environ.get('SUPER_ADMIN_EMAIL')
    password = os.environ.get('SUPER_ADMIN_PASSWORD')

    if not email or not password:
        return

    with app.app_context():
        try:
            # Check if users table exists to avoid errors during initial db init
            inspector = inspect(db.engine)
            if not inspector.has_table("users"):
                logger.warning("Database tables not found. Skipping Super Admin seed.")
                return

            user = User.query.filter_by(email=email).first()
            if not user:
                username = email.split('@')[0]
                # Ensure username is unique
                if User.query.filter_by(username=username).first():
                    username = f"{username}_admin"

                new_user = User(
                    username=username,
                    email=email,
                    role='superadmin',
                    is_active=True,
                    is_verified=True
                )
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                logger.info("Super Admin integrity check: Created new Super Admin.")
            else:
                logger.info("Super Admin integrity check: OK")
        except Exception as e:
            logger.error(f"Error seeding Super Admin: {e}")
