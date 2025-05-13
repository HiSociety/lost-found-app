from app import app, User

def check_admin_user():
    with app.app_context():
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if admin_user:
            print(f"Admin user found:")
            print(f"Name: {admin_user.name}")
            print(f"Email: {admin_user.email}")
            print(f"Is Admin: {admin_user.is_admin}")
        else:
            print("Admin user not found!")

if __name__ == '__main__':
    check_admin_user() 