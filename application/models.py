from .database import db
from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.Text, nullable=False)
    username = db.Column(db.Text, unique=True, nullable=False)
    #password = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.String(128))

# Create a Blog Post Model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255))