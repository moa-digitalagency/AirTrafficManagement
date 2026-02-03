import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models.base import db
from models.user import User, Role, Permission

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.getcwd(), 'instance/app.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev'
    db.init_app(app)
    return app

app = create_app()

def migrate_roles():
    with app.app_context():
        print("Creating new tables (roles, permissions)...")

        from sqlalchemy import event
        from sqlalchemy.schema import Table
        try:
            from geoalchemy2 import admin
            if admin:
                for ev in ['before_create', 'after_create', 'before_drop', 'after_drop']:
                    try: event.remove(Table, ev, getattr(admin, ev))
                    except: pass
        except ImportError:
            pass

        db.create_all()

        # Add role_id column to users table if missing
        from sqlalchemy import text
        try:
            db.session.execute(text("SELECT role_id FROM users LIMIT 1"))
        except:
            print("Adding role_id column to users table...")
            db.session.rollback()
            try:
                db.session.execute(text("ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id)"))
                db.session.commit()
            except Exception as e:
                print(f"Failed to add column: {e}")

        print("Seeding permissions...")
        resources = ['users', 'roles', 'flights', 'airports', 'airlines', 'aircraft', 'invoices', 'audit_logs', 'settings', 'languages']
        actions = ['read', 'create', 'update', 'delete']

        perms = {}
        for res in resources:
            for act in actions:
                p = Permission.query.filter_by(resource=res, action=act).first()
                if not p:
                    p = Permission(resource=res, action=act, description=f"{act.capitalize()} {res}")
                    db.session.add(p)
                perms[f"{res}:{act}"] = p

        # Add wildcard permissions
        p_wildcard = Permission.query.filter_by(resource='*', action='*').first()
        if not p_wildcard:
            p_wildcard = Permission(resource='*', action='*', description="Full Access")
            db.session.add(p_wildcard)
        perms['*:*'] = p_wildcard

        db.session.commit()

        print("Seeding roles...")
        roles_def = {
            'superadmin': ['*:*'],
            'observer': ['flights:read', 'airports:read', 'airlines:read', 'aircraft:read'],
            'supervisor': ['flights:*', 'airports:*', 'airlines:*', 'aircraft:*', 'invoices:read'],
            'controller': ['flights:*', 'airports:read', 'airlines:read', 'aircraft:read'],
            'billing': ['invoices:*', 'flights:read'],
            'auditor': ['audit_logs:read', 'users:read', 'flights:read', 'invoices:read']
        }

        created_roles = {}
        for role_name, perm_list in roles_def.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f"Role {role_name}", is_system=True)
                db.session.add(role)
                db.session.commit() # Commit to get ID

            # Assign permissions
            current_perms = list(role.permissions)
            for perm_str in perm_list:
                if perm_str == '*:*':
                    if p_wildcard not in current_perms:
                        role.permissions.append(p_wildcard)
                else:
                    if ':' in perm_str:
                        res, act = perm_str.split(':')
                        # Find matching permissions
                        if act == '*':
                            matches = [p for k, p in perms.items() if k.startswith(f"{res}:")]
                            for m in matches:
                                if m not in current_perms:
                                    role.permissions.append(m)
                        else:
                            p = perms.get(perm_str)
                            if p and p not in current_perms:
                                role.permissions.append(p)

            created_roles[role_name] = role

        db.session.commit()

        print("Migrating users...")
        users = User.query.filter(User.role_id == None).all()
        for user in users:
            if user.role and user.role in created_roles:
                user.role_id = created_roles[user.role].id
                print(f"Assigned role {user.role} to user {user.username}")

        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    migrate_roles()
