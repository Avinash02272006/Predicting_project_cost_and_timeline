
from passlib.hash import pbkdf2_sha256
from .database import User, db

def hash_password(password):
    return pbkdf2_sha256.hash(password)

def verify_password(password, hash):
    return pbkdf2_sha256.verify(password, hash)

def register_user(username, email, password):
    if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
        return False
    new_user = User(username=username, email=email, password_hash=hash_password(password))
    db.session.add(new_user)
    db.session.commit()
    return True

def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None
