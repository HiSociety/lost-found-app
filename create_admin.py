from app import app, db, User

def create_admin_user():
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(email='admin@example.com').first()
        
        if admin_user:
            print("Admin user already exists!")
            return
        
        # Create new admin user
        admin_user = User(
            email='admin@example.com',
            name='Admin',
            is_admin=True
        )
        
        # Set password using the proper method
        admin_user.set_password('admin123')
        
        # Add to database and commit
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully!")

if __name__ == '__main__':
    create_admin_user() 