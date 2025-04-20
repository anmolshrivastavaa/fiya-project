from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'leader' or 'contributor'

    # Relationships
    projects = db.relationship('Project', backref='leader', lazy=True)
    applications = db.relationship('Application', backref='contributor', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_score = db.Column(db.Integer, default=0)  # Optional, calculated as needed
    status = db.Column(db.String(50), default='open')  # e.g., 'open', 'closed'

    # Relationships
    applications = db.relationship('Application', backref='project', lazy=True)

    def __repr__(self):
        return f'<Project {self.title}>'

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contributor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    match_score = db.Column(db.Integer, nullable=False)  # Required field, must be calculated upon application

    def __repr__(self):
        return f'<Application contributor={self.contributor_id} project={self.project_id}>'

# Function to initialize the database
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
