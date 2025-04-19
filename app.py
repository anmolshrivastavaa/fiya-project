from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from models import db, User, Project, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize DB + Login Manager
init_db(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Home
@app.route('/')
def home():
    return render_template('index.html')


# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
    

      

        new_user = User(
            username=username,
            email=email,
            password=password,
            role=role,
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.role == 'leader':
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            new_project = Project(title=title, description=description, created_by=current_user.id)
            db.session.add(new_project)
            db.session.commit()
            flash('Project created successfully!', 'success')
        projects = Project.query.filter_by(created_by=current_user.id).all()
        return render_template('dashboard_leader.html', projects=projects, user=current_user)

    elif current_user.role == 'contributor':
        projects = Project.query.all()
        return render_template('dashboard_contributor.html', projects=projects, user=current_user)


# Create project route
@app.route('/create-project', methods=['GET', 'POST'])
@login_required
def create_project():
    if current_user.role != 'leader':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_project = Project(title=title, description=description, created_by=current_user.id)
        db.session.add(new_project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_project.html')


# Apply for project
@app.route('/project/<int:project_id>/apply', methods=['POST'])
@login_required
def apply_project(project_id):
    if current_user.role != 'contributor':
        return redirect(url_for('dashboard'))

    project = Project.query.get_or_404(project_id)

    if hasattr(project, 'status') and project.status == 'closed':
        flash('This project is no longer accepting applicants.', 'danger')
        return redirect(url_for('dashboard'))

    score = calculate_match_score(current_user, project)
    flash(f'You applied for {project.title} with a match score of {score}%', 'success')
    return redirect(url_for('dashboard'))


# Simple match score logic
def calculate_match_score(contributor, project):
    return 85


if __name__ == '__main__':
    app.run(debug=True)
