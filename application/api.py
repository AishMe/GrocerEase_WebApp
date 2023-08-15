from flask_restful import Resource, fields, marshal_with
from flask import request, jsonify, session
from flask import current_app as app
from werkzeug.security import generate_password_hash
from application.models import User, Category, Product
from application.validation import BusinessValidationError
from datetime import datetime
from .database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity


category_output_fields = {
    "section_id": fields.Integer,
    "name": fields.String,
    "cat_image": fields.String
}

product_output_fields = {
    "product_id": fields.Integer,
    "name": fields.String,
    "manufacture_date": fields.String,
    "rate_per_unit": fields.Float,
    "unit": fields.String,
    "stock": fields.Float,
    "image": fields.String,
    "section_id": fields.Integer
}

# Initialize the JWT manager
jwt = JWTManager(app)

# Set a secret key for JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key'

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Authenticate user (check email and password)
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.user_id)
        return {'access_token': access_token}, 200
    else:
        return {'message': 'Invalid credentials'}, 401

def login_required(role):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return {'error': 'Authentication required'}, 401
            user_id = session['user_id']
            user = User.query.get(user_id)
            if not user or (role == 'user' and user.is_manager) or (role == 'manager' and not user.is_manager):
                return {'error': 'Unauthorized'}, 403
            return f(*args, **kwargs)
        
        decorated_function.__name__ = f'{f.__name__}_{role}'
        return decorated_function
    
    return decorator


class UserAPI(Resource):

    # Create User
    def post(self):
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not (name and email and password):
            raise BusinessValidationError(status_code=400, error_code="BE1002", error_message="Required fields are missing")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise BusinessValidationError(status_code=409, error_code="BE1006", error_message="User with this email already exists")

        hashed_pw = generate_password_hash(password, method='sha256')
        new_user = User(name=name, email=email, password_hash=hashed_pw)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return {'message': 'User added successfully'}, 201
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1007", error_message="Failed to add user")
        
    # Update User
    def put(self, user_id):
        data = request.get_json()
        email = data.get('email')

        if not email:
            raise BusinessValidationError(status_code=400, error_code="BE1002", error_message="email is required")

        if "@" not in email:
            raise BusinessValidationError(status_code=400, error_code="BE1003", error_message="Invalid email")

        user = User.query.get_or_404(user_id)
        user.email = email

        try:
            db.session.commit()
            return {'message': 'User updated successfully'}, 200
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1008", error_message="Failed to update user")
        

    # Delete User
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)

        try:
            db.session.delete(user)
            db.session.commit()
            return {'message': 'User deleted successfully'}, 200
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1009", error_message="Failed to delete user")
    

class CategoryAPI(Resource):

    @marshal_with(category_output_fields)
    @jwt_required()
    def get(self, section_id=None):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if user.is_manager:
            if section_id is None:
                # Get All Categories for Managers (Showing section_id and name only)
                categories = Category.query.all()
                return categories
            else:
                # Get Category by section_id for Managers (Showing all information)
                category = Category.query.get_or_404(section_id)
                return category
        else:
            if section_id is None:
                # Get All Categories for Users (Showing section_id and name only)
                categories = Category.query.all()
                result = [{'section_id': category.section_id, 'name': category.name} for category in categories]
                return result
            else:
                # Get Category by section_id for Users (Showing selected information)
                category = Category.query.get_or_404(section_id)
                result = {
                    'section_id': category.section_id,
                    'name': category.name
                }
                return result


    # Create Category
    @jwt_required()  # Requires a valid access token
    def post(self):
        current_user_id = get_jwt_identity()

        # Check if the current user is a manager (is_manager=1)
        user = User.query.get(current_user_id)
        if not user.is_manager:
            return {'error': 'Only managers are allowed to add categories'}, 403
        
        data = request.get_json()
        name = data.get('name')
        cat_image = data.get('cat_image', '')

        if not (name):
            raise BusinessValidationError(status_code=400, error_code="BE1002", error_message="Required fields are missing")

        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            raise BusinessValidationError(status_code=409, error_code="BE1006", error_message="Category already exists")

        new_category = Category(name=name, cat_image=cat_image)

        
        try:
            db.session.add(new_category)
            db.session.commit()
            return {'message': 'Category added successfully'}, 201
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1007", error_message="Failed to add category")
        

    # Update Category
    @jwt_required()  # Requires a valid access token
    def put(self, section_id):
        current_user_id = get_jwt_identity()

        # Check if the current user is a manager (is_manager=1)
        user = User.query.get(current_user_id)
        if not user.is_manager:
            return {'error': 'Only managers are allowed to add categories'}, 403
        
        data = request.get_json()
        name = data.get('name')
        cat_image = data.get('cat_image')

        category = Category.query.get_or_404(section_id)

        # Update category attributes if provided
        if name:
            category.name = name
        if cat_image:
            category.cat_image = cat_image

        try:
            db.session.commit()
            return {'message': 'Category updated successfully'}, 200
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1008", error_message="Failed to update category")
        

    # Delete Category
    @jwt_required()  # Requires a valid access token
    def delete(self, section_id):
        current_user_id = get_jwt_identity()

        # Check if the current user is a manager (is_manager=1)
        user = User.query.get(current_user_id)
        if not user.is_manager:
            return {'error': 'Only managers are allowed to add categories'}, 403
        
        category = Category.query.get_or_404(section_id)

        try:
            db.session.delete(category)
            db.session.commit()
            return {'message': 'Category deleted successfully'}, 200
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1009", error_message="Failed to delete category")
    

class ProductAPI(Resource):

    @marshal_with(product_output_fields)
    @jwt_required()
    def get(self, product_id=None):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if user.is_manager:
            if product_id is None:
                # Get All Products for Managers (Showing product_id and name only)
                products = Product.query.all()
                return products
            else:
                # Get Product by product_id for Managers (Showing all information)
                product = Product.query.get_or_404(product_id)
                return product
        else:
            if product_id is None:
                # Get All Products for Users (Showing product_id and name only)
                products = Product.query.all()
                result = [{'product_id': product.product_id, 'name': product.name} for product in products]
                return result
            else:
                # Get Product by product_id for Users (Showing selected information)
                product = Product.query.get_or_404(product_id)
                result = {
                    'product_id': product.product_id,
                    'name': product.name,
                    'rate_per_unit': product.rate_per_unit,
                    'unit': product.unit,
                    'stock': product.stock,
                    'image': product.image
                }
                return result


    # Create Product
    @jwt_required()  # Requires a valid access token
    def post(self):
        current_user_id = get_jwt_identity()

        # Check if the current user is a manager (is_manager=1)
        user = User.query.get(current_user_id)
        if not user.is_manager:
            return {'error': 'Only managers are allowed to add products'}, 403
        
        data = request.get_json()
        name = data.get('name')
        manufacture_date = data.get('manufacture_date')
        rate_per_unit = data.get('rate_per_unit')
        unit = data.get('unit')
        stock = data.get('stock')
        image = data.get('image')
        section_id = data.get('section_id')

        if not name or not manufacture_date or not rate_per_unit or not unit or not stock or not section_id:
            raise BusinessValidationError(status_code=400, error_code="BE1002", error_message="Missing required fields")

        new_product = Product(
            name=name,
            manufacture_date=manufacture_date,
            rate_per_unit=rate_per_unit,
            unit=unit,
            stock=stock,
            image=image,
            section_id=section_id
        )

        try:
            db.session.add(new_product)
            db.session.commit()
            return {'message': 'Product added successfully'}, 201
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1010", error_message="Failed to add product")
        

    # Update Product
    @jwt_required()  # Requires a valid access token
    def put(self, product_id):
        current_user_id = get_jwt_identity()

        # Check if the current user is a manager (is_manager=1)
        user = User.query.get(current_user_id)
        if not user.is_manager:
            return {'error': 'Only managers are allowed to update products'}, 403
        
        data = request.get_json()
        name = data.get('name')
        manufacture_date = data.get('manufacture_date')
        rate_per_unit = data.get('rate_per_unit')
        unit = data.get('unit')
        stock = data.get('stock')
        image = data.get('image')
        section_id = data.get('section_id')

        product = Product.query.get_or_404(product_id)
        
        # Update product attributes if provided
        if name:
            product.name = name
        if manufacture_date:
            product.manufacture_date = manufacture_date
        if rate_per_unit:
            product.rate_per_unit = rate_per_unit
        if unit:
            product.unit = unit
        if stock:
            product.stock = stock
        if image:
            product.image = image
        if section_id:
            product.section_id = section_id

        try:
            db.session.commit()
            return {'message': 'Product updated successfully'}, 200
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1011", error_message="Failed to update product")

        

    # Delete Product
    @jwt_required()  # Requires a valid access token
    def delete(self, product_id):
        current_user_id = get_jwt_identity()

        # Check if the current user is a manager (is_manager=1)
        user = User.query.get(current_user_id)
        if not user.is_manager:
            return {'error': 'Only managers are allowed to delete products'}, 403

        product = Product.query.get_or_404(product_id)

        try:
            db.session.delete(product)
            db.session.commit()
            return {'message': 'Product deleted successfully'}, 200
        except:
            db.session.rollback()
            raise BusinessValidationError(status_code=500, error_code="BE1012", error_message="Failed to delete product")
