from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from models import db, User, Project, Application, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize DB + Login
init_db(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.role == 'leader':
        projects = Project.query.filter_by(created_by=current_user.id).all()

        project_applications = {}
        for project in projects:
            applications = Application.query.filter_by(project_id=project.id).all()
            applicants = []
            for app in applications:
                contributor = User.query.get(app.contributor_id)
                applicants.append({'username': contributor.username, 'match_score': app.match_score})
            project_applications[project.id] = applicants

        return render_template('dashboard_leader.html', projects=projects, project_applications=project_applications)

    elif current_user.role == 'contributor':
        projects = Project.query.all()
        project_data = []

        for project in projects:
            leader = User.query.get(project.created_by)
            project_data.append({
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'leader_name': leader.username if leader else 'Unknown'
            })

        return render_template('dashboard_contributor.html', projects=project_data)

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

@app.route('/project/<int:project_id>/apply', methods=['POST'])
@login_required
def apply_project(project_id):
    if current_user.role != 'contributor':
        return redirect(url_for('dashboard'))

    project = Project.query.get_or_404(project_id)

    existing = Application.query.filter_by(contributor_id=current_user.id, project_id=project_id).first()
    if existing:
        flash('You already applied to this project.', 'warning')
        return redirect(url_for('dashboard'))

    score = calculate_match_score(current_user, project)

    application = Application(
        contributor_id=current_user.id,
        project_id=project_id,
        match_score=score
    )
    db.session.add(application)
    db.session.commit()

    flash(f'Applied to "{project.title}" with a match score of {score}%', 'success')
    return redirect(url_for('dashboard'))

@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.id != project.created_by:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard'))

    Application.query.filter_by(project_id=project_id).delete()
    db.session.delete(project)
    db.session.commit()

    flash('Project deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)

    if current_user.id != project.created_by:
        flash('You are not authorized to edit this project.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        project.title = request.form['title']
        project.description = request.form['description']
        db.session.commit()

        flash('Project updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_project.html', project=project)

@app.route('/project/<int:project_id>/applicants', methods=['GET'])
@login_required
def view_applicants(project_id):
    project = Project.query.get_or_404(project_id)

    if current_user.id != project.created_by:
        flash('You are not authorized to view applicants for this project.', 'danger')
        return redirect(url_for('dashboard'))

    applications = Application.query.filter_by(project_id=project.id).all()
    applicants = []
    for app in applications:
        contributor = User.query.get(app.contributor_id)
        applicants.append({'username': contributor.username, 'match_score': app.match_score})

    return render_template('view_applicants.html', project=project, applicants=applicants)

def calculate_match_score(contributor, project):
    return 85  # Replace with real logic

if __name__ == '__main__':
    app.run(debug=True,port=5000)
