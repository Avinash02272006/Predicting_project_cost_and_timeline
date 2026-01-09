
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    history = db.relationship('History', backref='user', lazy=True)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    project_type = db.Column(db.String(50))
    predicted_cost = db.Column(db.Float)
    predicted_timeline = db.Column(db.Float)
    suggestion = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
