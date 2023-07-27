from .database import db
from datetime import datetime

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    username = db.Column(db.Text, unique=True, nullable=False)
    #password = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.String(128))

class Category(db.Model):
    section_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    manufacture_date = db.Column(db.Text, nullable=False)
    rate_per_unit = db.Column(db.REAL, nullable=False)
    unit = db.Column(db.Text, nullable=False)
    stock = db.Column(db.REAL, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('category.section_id'), nullable=False)

class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))
    quantity = db.Column(db.Integer)