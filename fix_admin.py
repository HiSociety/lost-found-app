from app import app, db, User

def fix_admin_user():
    with app.app_context():
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if admin_user:
            admin_user.is_admin = True
            db.session.commit()
            print("Admin status updated successfully!")
        else:
            print("Admin user not found!")

if __name__ == '__main__':
    fix_admin_user() 