from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import jwt
from time import time
from flask import current_app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    success_story = db.Column(db.Boolean, default=False)  # True if it's a success story
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('testimonials', lazy=True))
    item = db.relationship('Item', backref=db.backref('testimonials', lazy=True))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiration = db.Column(db.DateTime)
    rating_received = db.Column(db.Float, default=0.0)  # Average rating received
    rating_count = db.Column(db.Integer, default=0)     # Number of ratings received
    helper_points = db.Column(db.Integer, default=0)    # Points earned for helping others
    
    def update_rating(self, new_rating):
        total_rating = (self.rating_received * self.rating_count) + new_rating
        self.rating_count += 1
        self.rating_received = total_rating / self.rating_count
        db.session.commit()

    def add_helper_points(self, points):
        self.helper_points += points
        db.session.commit()

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                          algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password) 