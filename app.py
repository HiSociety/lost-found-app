from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, MultipleFileField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from functools import wraps
import pytz
import click
from PIL import Image as PILImage
from flask_caching import Cache
import io
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
from flask_mail import Mail, Message
import jwt
from time import time
from flask import current_app

def send_password_reset_email(user, token):
    msg = Message('Password Reset Request',
                  sender=app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    try:
        mail.send(msg)
    except Exception as e:
        app.logger.error(f'Failed to send password reset email: {str(e)}')
        flash('Failed to send password reset email. Please try again later.', 'error')
        return redirect(url_for('reset_password'))

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_found.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session timeout

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')  # Use the same email as username

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)
mail = Mail(app)

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/security.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Lost and Found startup')

# Initialize cache
cache = Cache(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Context processor to make current year available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    items = db.relationship('Item', backref='owner', lazy=True)
    rating_received = db.Column(db.Float, default=0.0, nullable=False)  # Make it non-nullable with default 0.0
    rating_count = db.Column(db.Integer, default=0, nullable=False)     # Make it non-nullable with default 0
    helper_points = db.Column(db.Integer, default=0, nullable=False)    # Make it non-nullable with default 0
    is_admin = db.Column(db.Boolean, default=False)  # Add admin flag
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)  # Add date_joined field

    @property
    def formatted_rating(self):
        """Return formatted rating or 'No ratings' if no ratings received"""
        if self.rating_count == 0 or self.rating_received is None:
            return "No ratings"
        try:
            return f"{float(self.rating_received):.1f}"
        except (TypeError, ValueError):
            return "No ratings"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_rating(self, new_rating):
        if not isinstance(new_rating, (int, float)) or new_rating < 1 or new_rating > 5:
            raise ValueError("Rating must be a number between 1 and 5")
        
        # Initialize rating_received if it's None
        if self.rating_received is None:
            self.rating_received = 0.0
        if self.rating_count is None:
            self.rating_count = 0
            
        total_rating = (self.rating_received * self.rating_count) + new_rating
        self.rating_count += 1
        self.rating_received = total_rating / self.rating_count
        db.session.commit()

    def add_helper_points(self, points):
        if not isinstance(points, int) or points < 0:
            raise ValueError("Points must be a positive integer")
        
        # Initialize helper_points if it's None
        if self.helper_points is None:
            self.helper_points = 0
            
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

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)  # Make item_id optional
    content = db.Column(db.Text, nullable=False)
    success_story = db.Column(db.Boolean, default=False)  # True if it's a success story
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('testimonials', lazy=True))
    item = db.relationship('Item', backref=db.backref('testimonials', lazy=True))

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(20), nullable=False)
    unique_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    contact_details = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    is_claimed = db.Column(db.Boolean, default=False)
    removal_date = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    images = db.relationship('Image', backref='item', lazy=True)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Form Classes
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class PostItemForm(FlaskForm):
    document_type = SelectField('Document Type', 
        choices=[
            ('national_id', 'National ID'),
            ('passport', 'Passport'),
            ('drivers_license', "Driver's License"),
            ('other', 'Other')
        ],
        validators=[DataRequired()]
    )
    unique_id = StringField('Document ID Number', validators=[DataRequired()])
    name = StringField('Document Holder Name', validators=[DataRequired()])
    description = TextAreaField('Additional Details')
    contact_details = TextAreaField('Contact Information', validators=[DataRequired()])
    images = MultipleFileField('Upload Images')
    submit = SubmitField('Post Document')

class SearchForm(FlaskForm):
    search_query = StringField('Search')
    document_type = SelectField('Document Type', 
        choices=[
            ('', 'All Types'),
            ('national_id', 'National ID'),
            ('passport', 'Passport'),
            ('drivers_license', "Driver's License"),
            ('other', 'Other')
        ]
    )
    submit = SubmitField('Search')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

def compress_image(image_data, max_size=(800, 800), quality=85):
    """Compress image while maintaining aspect ratio"""
    img = PILImage.open(io.BytesIO(image_data))
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        img = img.convert('RGB')
    
    # Calculate new dimensions while maintaining aspect ratio
    width, height = img.size
    if width > max_size[0] or height > max_size[1]:
        ratio = min(max_size[0]/width, max_size[1]/height)
        new_size = (int(width*ratio), int(height*ratio))
        img = img.resize(new_size, PILImage.Resampling.LANCZOS)
    
    # Save compressed image
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    return output.getvalue()

@app.route('/')
def home():
    stats = get_document_statistics()
    return render_template('home.html', stats=stats)

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post_item():
    form = PostItemForm()
    if form.validate_on_submit():
        item = Item(
            document_type=form.document_type.data,
            unique_id=form.unique_id.data,
            name=form.name.data,
            description=form.description.data,
            contact_details=form.contact_details.data,
            user_id=current_user.id
        )
        
        # Handle image uploads with compression
        for image in form.images.data:
            if image and image.filename:
                filename = secure_filename(image.filename)
                # Read the image data
                image_data = image.read()
                # Compress the image
                compressed_data = compress_image(image_data)
                # Save the compressed image
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'wb') as f:
                    f.write(compressed_data)
                img = Image(filename=filename, item=item)
                db.session.add(img)

        db.session.add(item)
        db.session.commit()
        flash('Document posted successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('post_item.html', form=form)

@app.route('/search', methods=['GET', 'POST'])
def search_item():
    form = SearchForm()
    search_performed = False
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    if form.validate_on_submit():
        search_performed = True
        query = Item.query
        
        if form.document_type.data:
            query = query.filter_by(document_type=form.document_type.data)
        
        if form.search_query.data:
            search_query = form.search_query.data
            query = query.filter(
                db.or_(
                    Item.unique_id.ilike(f'%{search_query}%'),
                    Item.name.ilike(f'%{search_query}%')
                )
            )
        
        items = query.order_by(Item.date_posted.desc()).paginate(page=page, per_page=per_page)
        return render_template('search.html', form=form, items=items, search_performed=search_performed)
    
    return render_template('search.html', form=form, items=[], search_performed=search_performed)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            log_security_event('login_success', user.id)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            log_security_event('login_failed', None, {'email': form.email.data})
            flash('Invalid email or password.', 'error')
            
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
            
        user = User(email=form.email.data, name=form.name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/get_contact_details/<int:item_id>')
@login_required
def get_contact_details(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify({
        'contact_details': item.contact_details
    })

def remove_old_claimed_items():
    with app.app_context():
        current_time = datetime.utcnow()
        items_to_remove = Item.query.filter(
            Item.is_claimed == True,
            Item.removal_date <= current_time
        ).all()
        
        for item in items_to_remove:
            # Delete associated images first
            for image in item.images:
                try:
                    # Delete image file from uploads folder
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"Error deleting image {image.filename}: {e}")
                db.session.delete(image)
            
            db.session.delete(item)
        
        db.session.commit()

# Initialize the scheduler with UTC timezone
scheduler = BackgroundScheduler(timezone=pytz.UTC)
scheduler.start()

# Add the job to remove old claimed items
scheduler.add_job(remove_old_claimed_items, 'interval', hours=1)

@app.route('/mark_as_claimed/<int:item_id>', methods=['POST'])
@login_required
@csrf.exempt  # Temporarily disable CSRF for testing
def mark_as_claimed(item_id):
    try:
        item = Item.query.get_or_404(item_id)
        
        # Check if item is already claimed
        if item.is_claimed:
            return jsonify({
                'status': 'error',
                'message': 'This document has already been claimed.'
            }), 400
            
        # Update item status
        item.is_claimed = True
        item.removal_date = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Document has been marked as claimed and will be removed after 24 hours.'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error marking item as claimed: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to claim item. Please try again.'
        }), 500

@app.route('/community')
def community():
    # Get success stories (testimonials marked as success stories)
    success_stories = Testimonial.query.filter_by(success_story=True).order_by(Testimonial.date_posted.desc()).limit(5).all()
    
    # Get recent testimonials
    testimonials = Testimonial.query.filter_by(success_story=False).order_by(Testimonial.date_posted.desc()).limit(10).all()
    
    # Get top helpers (users with highest helper points)
    top_helpers = User.query.order_by(User.helper_points.desc()).limit(5).all()
    
    return render_template('community.html', 
                         success_stories=success_stories,
                         testimonials=testimonials,
                         top_helpers=top_helpers)

@app.route('/submit_testimonial', methods=['POST'])
@login_required
def submit_testimonial():
    content = request.form.get('content')
    rating = int(request.form.get('rating'))
    is_success_story = request.form.get('is_success_story') == 'on'
    
    if not content or not rating:
        flash('Please provide both content and rating.', 'error')
        return redirect(url_for('community'))
    
    if rating < 1 or rating > 5:
        flash('Rating must be between 1 and 5.', 'error')
        return redirect(url_for('community'))
    
    # Create the testimonial
    testimonial = Testimonial(
        user_id=current_user.id,
        content=content,
        rating=rating,
        success_story=is_success_story
    )
    
    # Update user's rating
    current_user.update_rating(rating)
    
    # If it's a success story, add helper points
    if is_success_story:
        current_user.add_helper_points(10)
    
    db.session.add(testimonial)
    db.session.commit()
    
    flash('Thank you for sharing your experience!', 'success')
    return redirect(url_for('community'))

# Add route for community guidelines
@app.route('/guidelines')
def guidelines():
    return render_template('guidelines.html')

# Add admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get statistics
    total_users = User.query.count()
    total_items = Item.query.count()
    claimed_items = Item.query.filter_by(is_claimed=True).count()
    total_testimonials = Testimonial.query.count()

    # Get document type distribution
    doc_stats = {
        'national_id': Item.query.filter_by(document_type='national_id').count(),
        'passport': Item.query.filter_by(document_type='passport').count(),
        'drivers_license': Item.query.filter_by(document_type='drivers_license').count(),
        'other': Item.query.filter_by(document_type='other').count()
    }

    # Get recent activity with pagination
    items_page = request.args.get('items_page', 1, type=int)
    users_page = request.args.get('users_page', 1, type=int)
    testimonials_page = request.args.get('testimonials_page', 1, type=int)

    recent_items = Item.query.order_by(Item.date_posted.desc()).paginate(page=items_page, per_page=5)
    recent_users = User.query.order_by(User.date_joined.desc()).paginate(page=users_page, per_page=5)
    recent_testimonials = Testimonial.query.order_by(Testimonial.date_posted.desc()).paginate(page=testimonials_page, per_page=5)

    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_items=total_items,
                         claimed_items=claimed_items,
                         total_testimonials=total_testimonials,
                         doc_stats=doc_stats,
                         recent_items=recent_items,
                         recent_users=recent_users,
                         recent_testimonials=recent_testimonials)

@app.route('/admin/users')
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.date_joined.desc()).paginate(page=page, per_page=10)
    return render_template('admin/users.html', users=users)

@app.route('/admin/items')
@admin_required
def admin_items():
    page = request.args.get('page', 1, type=int)
    items = Item.query.order_by(Item.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('admin/items.html', items=items)

@app.route('/admin/testimonials')
@admin_required
def admin_testimonials():
    page = request.args.get('page', 1, type=int)
    testimonials = Testimonial.query.order_by(Testimonial.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('admin/testimonials.html', testimonials=testimonials)

@app.route('/admin/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'User {user.name} admin status has been updated.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_item/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    # Delete associated images
    for image in item.images:
        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image {image.filename}: {e}")
        db.session.delete(image)
    
    db.session.delete(item)
    db.session.commit()
    flash('Item has been deleted.', 'success')
    return redirect(url_for('admin_items'))

@app.route('/admin/delete_testimonial/<int:testimonial_id>', methods=['POST'])
@login_required
@admin_required
def delete_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    db.session.delete(testimonial)
    db.session.commit()
    flash('Testimonial has been deleted.', 'success')
    return redirect(url_for('admin_testimonials'))

# Add this before the if __name__ == '__main__': block
@app.cli.command("create-admin")
def create_admin():
    """Create an admin user"""
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin:
        click.echo('Admin user already exists!')
        return
    
    admin = User(
        email='admin@example.com',
        name='Admin',
        is_admin=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    click.echo('Admin user created successfully!')

# Add caching for frequently accessed data
@cache.memoize(timeout=300)
def get_document_statistics():
    # Get counts for National IDs
    national_ids_total = Item.query.filter_by(document_type='national_id').count()
    national_ids_claimed = Item.query.filter_by(document_type='national_id', is_claimed=True).count()
    national_ids_unclaimed = national_ids_total - national_ids_claimed

    # Get counts for Passports
    passports_total = Item.query.filter_by(document_type='passport').count()
    passports_claimed = Item.query.filter_by(document_type='passport', is_claimed=True).count()
    passports_unclaimed = passports_total - passports_claimed

    return {
        'national_ids': {
            'total': national_ids_total,
            'claimed': national_ids_claimed,
            'unclaimed': national_ids_unclaimed
        },
        'passports': {
            'total': passports_total,
            'claimed': passports_claimed,
            'unclaimed': passports_unclaimed
        }
    }

@app.route('/get_item_details/<int:item_id>')
@login_required
def get_item_details(item_id):
    item = Item.query.get_or_404(item_id)
    images = [img.filename for img in item.images]
    return jsonify({
        'unique_id': item.unique_id,
        'name': item.name,
        'description': item.description,
        'images': images
    })

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Add security logging
def log_security_event(event_type, user_id=None, details=None):
    app.logger.info(f'Security Event: {event_type} - User: {user_id} - Details: {details}')

# Apply rate limits to API endpoints
@app.route('/api/documents/search', methods=['GET'])
@limiter.limit("10 per minute")
def api_search_documents():
    search_query = request.args.get('q', '')
    document_type = request.args.get('type', '')
    
    query = Item.query.filter(Item.is_claimed == False)
    
    if search_query:
        query = query.filter(
            db.or_(
                Item.unique_id.ilike(f'%{search_query}%'),
                Item.name.ilike(f'%{search_query}%')
            )
        )
    
    if document_type:
        query = query.filter_by(document_type=document_type)
    
    items = query.order_by(Item.date_posted.desc()).all()
    
    return jsonify({
        'items': [{
            'id': item.id,
            'document_type': item.document_type,
            'unique_id': item.unique_id,
            'name': item.name,
            'description': item.description,
            'date_posted': item.date_posted.isoformat()
        } for item in items]
    })

@app.route('/api/documents', methods=['POST'])
@limiter.limit("5 per minute")
def api_post_document():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['document_type', 'unique_id', 'name', 'contact_details']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    item = Item(
        document_type=data['document_type'],
        unique_id=data['unique_id'],
        name=data['name'],
        description=data.get('description', ''),
        contact_details=data['contact_details'],
        user_id=current_user.id
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({
        'message': 'Document posted successfully',
        'item_id': item.id
    }), 201

@app.route('/api/documents/<int:document_id>/claim', methods=['POST'])
@limiter.limit("3 per minute")
def api_claim_document(document_id):
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    item = Item.query.get_or_404(document_id)
    if item.is_claimed:
        return jsonify({'error': 'Document already claimed'}), 400
    
    item.is_claimed = True
    item.removal_date = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()
    
    return jsonify({
        'message': 'Document claimed successfully',
        'item_id': item.id
    })

# Example usage in password reset
@app.route('/reset_password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate reset token
            token = user.get_reset_password_token()
            # Send reset email
            send_password_reset_email(user, token)
            log_security_event('password_reset_requested', user.id)
            flash('Password reset instructions sent to your email')
            return redirect(url_for('login'))
        else:
            log_security_event('password_reset_failed', None, {'email': form.email.data})
            flash('Email not found')
    
    return render_template('reset_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired token')
        return redirect(url_for('reset_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    
    return render_template('reset_password_token.html', form=form, token=token)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5002) 