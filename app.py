from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Chemin vers ta base de données
app.secret_key = 'your_secret_key'  # Remplace par une clé secrète appropriée
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Met à True en production avec HTTPS

# Initialiser les extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)  # Protection CSRF
limiter = Limiter(get_remote_address, app=app)  # Limite les requêtes par adresse IP

# Modèle de base de données pour les utilisateurs
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Route d'inscription avec protection CSRF
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Vérifie si l'email ou le nom d'utilisateur existe déjà
        if User.query.filter_by(email=email).first():
            flash("Email déjà utilisé.", "danger")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash("Nom d'utilisateur déjà pris.", "danger")
            return redirect(url_for('register'))

        # Hachage du mot de passe
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Inscription réussie !", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Route de connexion avec limite de tentatives
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id  # Utilise l'ID utilisateur dans la session
            flash("Connexion réussie !", "success")
            return redirect(url_for('index'))  # Redirige vers la page d'accueil après connexion
        flash("Identifiants incorrects.", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')

# Route de profil
@app.route('/profile', methods=['GET'])
def profile():
    user_id = session.get('user_id')  # Récupère l'ID utilisateur de la session
    if not user_id:
        return redirect(url_for('login'))  # Redirige vers la connexion si pas d'ID

    user = User.query.get(user_id)
    return render_template('profile.html', user=user)

# Déconnexion
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)  # Supprime l'ID utilisateur de la session
    flash("Déconnexion réussie !", "success")
    return redirect(url_for('index'))  # Redirige vers la page d'accueil

# Route d'accueil
@app.route('/')
def index():
    return render_template('index.html')  # Change en fonction de ta page d'accueil

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crée les tables si elles n'existent pas déjà
    app.run(debug=True)
