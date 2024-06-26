from .database import db
from datetime import datetime

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    username = db.Column(db.Text, unique=True, nullable=False)
    is_manager = db.Column(db.Integer, default=0)
    #password = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.String(128))

class Category(db.Model):
    section_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    cat_image = db.Column(db.Text)

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    manufacture_date = db.Column(db.Text, nullable=False)
    rate_per_unit = db.Column(db.REAL, nullable=False)
    unit = db.Column(db.Text, nullable=False)
    stock = db.Column(db.REAL, nullable=False)
    image = db.Column(db.Text)
    section_id = db.Column(db.Integer, db.ForeignKey('category.section_id'), nullable=False)

class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('category.section_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Orders(db.Model):
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False, default=0)
    order_number = db.Column(db.Integer, nullable=False)
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.cart_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('category.section_id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
