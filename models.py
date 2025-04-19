# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'leader' or 'contributor'

    projects = db.relationship('Project', backref='leader', lazy=True)

     # Required methods for Flask-Login
    def is_authenticated(self):
        return True

    def is_active(self):
        return True  # User is always active, can be changed based on your use case

    def is_anonymous(self):
        return False  # Not anonymous for normal users

    def get_id(self):
        return str(self.id)  # Return user ID as string (Flask-Login needs this)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='open')

    def __repr__(self):
        return f'<Project {self.title}>'

# Function to initialize the database (this creates tables)
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Creates the tables in the database


