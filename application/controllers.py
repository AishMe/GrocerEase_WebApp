from flask import Flask, session, request, redirect, render_template, url_for, flash
from flask import current_app as app
from .database import db
from application.models import User, Category, Product, Cart, Orders
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app.config['SECRET_KEY'] = "harekrishna"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.sqlite3'


# Create a User Form
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password_hash = PasswordField("Password", validators=[DataRequired(), EqualTo('password_hash_confirm', message='Both Passwords must Match!')])
    password_hash_confirm = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a Password Form
class PasswordForm(FlaskForm):
    email = StringField("Enter Email ID", validators=[DataRequired()])
    password_hash = PasswordField("Enter password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a Category Form
class CategoryForm(FlaskForm):
    category_name = StringField("Enter the Category Name", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a Product Form
class ProductForm(FlaskForm):
    product_name = StringField("Product Name", validators=[DataRequired()])
    rate = StringField("Rate", validators=[DataRequired()])
    stock = StringField("Stock", validators=[DataRequired()])
    unit = StringField("Unit", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a Namer Form
class NamerForm(FlaskForm):
    name = StringField("What's your name?", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a Cart Form
class AddToCartForm(FlaskForm):
    quantity = StringField("Quantity", validators=[DataRequired()])
    submit = SubmitField("Submit")



def login_required(role):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for(f'{role}_login', next=request.url))
            user_id = session['user_id']
            user = User.query.get(user_id)
            if not user or (role == 'user' and user.is_manager) or (role == 'manager' and not user.is_manager):
                return redirect(url_for(f'{role}_login', next=request.url))
            return f(*args, **kwargs)
        
        # Set a unique endpoint name based on the function name and role
        decorated_function.__name__ = f'{f.__name__}_{role}'
        return decorated_function
    
    return decorator



# Password Hashing Stuffs
@property
def password(self):
    raise AttributeError("Password is not a readable atrribute!")

@password.setter
def password(self, password):
    self.password_hash = generate_password_hash(password)

def verify_password(self, password):
    return check_password_hash(self.password_hash, password)


# JSON Demo
@app.route('/pizza')
def fav_pizzas_list():
    favorite_pizza = {
        "Harry": "Peparoni", 
        "Ammu": "Cheeze", 
        "Ria": "Pinapple"
    }
    return favorite_pizza

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/user_register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists. Please choose a different username."

        # Create a new user and add it to the database
        new_user = User(username=username, password=password, role='User')
        db.session.add(new_user)
        db.session.commit()

        # Redirect to user login page
        return redirect('/user_login')

    return render_template('user_register.html')


# Create Custom Error Pages

# Invalid Page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error404.html'), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template('error500.html'), 500


# Create Password Test Page
@app.route('/test_pw', methods=["GET", "POST"])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()

    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        # Clear the Form
        form.email.data = ''
        form.password_hash.data = ''
        #flash("Registration Successful!!")

    pw_to_check = User.query.filter_by(email=email).first()

    if pw_to_check is not None:
        passed = check_password_hash(pw_to_check.password_hash, password)
    else:
    # Handle the case when the user doesn't exist
        passed = False
    
    return render_template('test_pw.html', 
                           email = email,
                           password = password,  
                           pw_to_check = pw_to_check, 
                           passed = passed, 
                           form = form)


# Create Name Page
@app.route('/name', methods=["GET", "POST"])
def name():
    name = None
    form = NamerForm()

    # Validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Registration Successful!!")

    return render_template('name.html', 
                           name = name, 
                           form = form)


@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = User(name=form.name.data, email=form.email.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.email.data = ''
        form.password_hash.data = ''
        flash('User Added Successfully!')
    all_users = User.query.order_by(User.date_added)
    return render_template('add_user.html', 
                           form=form, 
                           name=name, 
                           all_users=all_users)


# Update Database Record
@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update(user_id):
    form = UserForm()
    name_to_update = User.query.get_or_404(user_id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        try: 
            db.session.commit()
            flash('User Updated Successfully!')
            return render_template('update.html', 
                                   form=form, 
                                   name_to_update=name_to_update, 
                                   user_id=user_id)
    
        except: 
            flash('Error! Looks like there was a problem. Please try again...')
            return render_template('update.html', 
                                   form=form, 
                                   name_to_update=name_to_update, 
                                   user_id=user_id)
    
    else:
        return render_template('update.html', 
                                   form=form, 
                                   name_to_update=name_to_update, 
                                   user_id=user_id)


# Delete a User from the Database Record
@app.route('/delete/<int:user_id>')
def delete(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    name = None
    form = UserForm()

    try: 
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("Account Deleted Successfully!")

        all_users = User.query.order_by(User.date_added)
        return render_template('add_user.html', 
                           form=form, 
                           name=name, 
                           all_users=all_users)

    except: 
        flash("Woops! There was a problem deleting the account. Please try again...")
        return render_template('add_user.html', 
                           form=form, 
                           name=name, 
                           all_users=all_users)



# Show the Categories and Products on the Manager Dashboard
@app.route('/manager_dashboard', endpoint='manager_dashboard')
@login_required(role='manager')
def manager_dashboard():
    # Grab all the posts from the database
    prod_count = Product.query.count()
    categories = Category.query.order_by(Category.section_id).all()

    # Create a dictionary to store products per category
    products_by_category = {}

    # Fetch products for each category and store them in the dictionary
    for category in categories:
        products = Product.query.filter_by(section_id=category.section_id).all()
        products_by_category[category.section_id] = products

    return render_template('manager_dashboard.html', 
                           products=products, 
                           categories=categories, 
                           prod_count=prod_count, 
                           products_by_category=products_by_category)


# Show the Categories and Products on the User Dashboard
@app.route('/user_dashboard', methods=['GET', 'POST'], endpoint='user_dashboard')
@login_required(role='user')
def user_dashboard():
    # Grab all the categories from the database
    categories = Category.query.order_by(Category.section_id).all()

    # Create a dictionary to store products per category
    products_by_category = {}

    # Fetch products for each category and store them in the dictionary
    for category in categories:
        products = Product.query.filter_by(section_id=category.section_id).all()
        products_by_category[category.section_id] = products

    return render_template('user_dashboard.html', products_by_category=products_by_category, categories=categories)


# Add Category
@app.route('/manager/add_category', methods=['GET', 'POST'])
def add_category():
    name = None
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category.query.filter_by(name=form.cat_name.data).first()
        if category is None:
            category = Category(name=form.cat_name.data)
            db.session.add(category)
            db.session.commit()
        name = form.cat_name.data
        form.cat_name.data = ''
        flash('Category Added Successfully!')
    all_categories = Category.query.order_by(Category.section_id)
    return render_template('add_category.html', 
                           form=form, 
                           name=name, 
                           all_categories=all_categories)


# Update Database Record in Category
@app.route('/update_category/<int:section_id>', methods=['GET', 'POST'])
def update_category(section_id):
    category_to_update = Category.query.get_or_404(section_id)
    form = CategoryForm()

    if form.validate_on_submit():
        category_to_update.name = form.category_name.data

        # Update the Database
        db.session.add(category_to_update)
        db.session.commit()

        flash("Category Information Has Been Updated!")
        return redirect(url_for('manager_dashboard', section_id=section_id))
    
    form.category_name.data = category_to_update.name

    return render_template('add_category.html', form=form)


# Delete a Category from the Database Record
@app.route('/delete_category/<int:section_id>')
def delete_category(section_id):
    category_to_delete = Category.query.get_or_404(section_id)

    try: 
        db.session.delete(category_to_delete)
        db.session.commit()
        flash("Category Deleted Successfully!")

        return redirect(url_for('manager_dashboard'))

    except: 
        flash("Woops! There was a problem deleting the category. Please try again...")
        return redirect(url_for('manager_dashboard'))



# Add a Product to the Database
@app.route('/<int:section_id>/add_product', methods=['GET', 'POST'])
def add_product(section_id):
    form = ProductForm()
    category_name = Category.query.get_or_404(section_id).name
    if form.validate_on_submit():
        # Here, you can save the product details to the database
        product = Product(
            name=form.product_name.data,
            rate_per_unit=form.rate.data,
            stock=form.stock.data,
            unit=form.unit.data, 
            manufacture_date = datetime.today().strftime('%d-%m-%y'), 
            section_id = section_id
        )

        db.session.add(product)
        db.session.commit()

        form.product_name.data = ''
        form.rate.data = ''
        form.stock.data = ''
        form.unit.data = ''

        flash('Product Added Successfully!')
        return redirect(url_for('manager_dashboard'))

    return render_template('add_product.html', 
                           form=form, 
                           section_id=section_id, 
                           category_name=category_name)


# Update Database Record in Product
@app.route('/update_product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    product_to_update = Product.query.get_or_404(product_id)
    form = ProductForm()

    if form.validate_on_submit():
        product_to_update.name = form.product_name.data
        product_to_update.rate_per_unit = form.rate.data
        product_to_update.unit = form.unit.data
        product_to_update.stock = form.stock.data

        # Update the Database
        db.session.add(product_to_update)
        db.session.commit()

        flash("Product Information Has Been Updated!")
        return redirect(url_for('manager_dashboard', product_id=product_id))
    
    form.product_name.data = product_to_update.name
    form.rate.data = product_to_update.rate_per_unit
    form.unit.data = product_to_update.unit
    form.stock.data = product_to_update.stock

    return render_template('add_product.html', form=form)



# Delete a Product from the Database Record
@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    product_to_delete = Product.query.get_or_404(product_id)

    try: 
        db.session.delete(product_to_delete)
        db.session.commit()
        flash("Product Deleted Successfully!")

        return redirect(url_for('manager_dashboard'))

    except: 
        flash("Woops! There was a problem deleting the product. Please try again...")
        return redirect(url_for('manager_dashboard'))





@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    form = PasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''

        user = User.query.filter_by(email=email, is_manager=0).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('user_login.html', form=form)


@app.route('/manager/login', methods=['GET', 'POST'])
def manager_login():
    form = PasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''

        manager = User.query.filter_by(email=email, is_manager=1).first()

        if manager and check_password_hash(manager.password_hash, password):
            session['user_id'] = manager.user_id
            flash("You Are Logged In As Manager!!")
            return redirect(url_for('manager_dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('manager_login.html', form=form)


@app.route('/manager')
def manager_page():
    if 'user_id' in session:
        user_id = session['user_id']
        manager = User.query.get(user_id)
        if manager and manager.is_manager:
            return render_template('manager.html', manager=manager)
    return redirect(url_for('manager_login'))


@app.route('/user')
def user_page():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user and not user.is_manager:
            return render_template('user.html', user=user)
    return redirect(url_for('user_login'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

'''
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_name = request.form.get('product_name')
    quantity = int(request.form.get('quantity'))

    # Save the cart item to the database
    cart_item = CartItem(product_name=product_name, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()

    flash("Item added to Cart Successfully", "success")
    return redirect(url_for('user_dashboard'))

@app.route('/buy_item', methods=['POST'])
def buy_item():
    product_name = request.form.get('product_name')
    quantity = int(request.form.get('quantity'))

    # Create a new purchase item
    purchase_item = PurchaseItem(product_name=product_name, quantity=quantity)
    db.session.add(purchase_item)
    db.session.commit()

    flash("Item bought Successfully", "success")
    return redirect(url_for('user_dashboard'))
'''


@app.route('/cart', endpoint='cart')
@login_required('user')
def cart():
    current_user_id = session['user_id']

    # Fetch cart items specific to the current user and perform a join with Product and Category tables
    cart_items = db.session.query(Cart, Product, Category).join(Product, Cart.product_id == Product.product_id).join(Category, Product.section_id == Category.section_id).filter(Cart.user_id == current_user_id).all()

    # Create a list to store cart item details
    cart_data = []

    # Calculate total price for each cart item and store in cart_data list
    for cart, product, category in cart_items:
        total_price = product.rate_per_unit * cart.quantity
        cart_data.append({
            'product_name': product.name,
            'category_name': category.name,
            'quantity': cart.quantity,
            'rate_per_unit': product.rate_per_unit,
            'total_price': total_price,
            'image': category.image
        })

    # Calculate overall total price
    total_price = sum(item['total_price'] for item in cart_data)

    return render_template('cart.html', cart_data=cart_data, total_price=total_price)



@app.route('/checkout', endpoint='checkout')
@login_required('user')
def checkout():
    user_id = session['user_id']

    # Get all cart items for the current user
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    # If the cart is empty, show a flash message and redirect to the cart page
    if not cart_items:
        flash('Your cart is empty. Add items to proceed with the checkout.', 'warning')
        return redirect(url_for('cart'))

    # Get the maximum order number for the current user
    max_order_number = Orders.query.filter_by(user_id=user_id).order_by(Orders.order_number.desc()).first()

    # Calculate the current_order_number
    if max_order_number:
        current_order_number = max_order_number.order_number + 1
    else:
        current_order_number = 1

    # Create new order records for each cart item
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)

        # Create a new order record
        order = Orders(
            order_number=current_order_number,
            user_id=user_id,
            cart_id=cart_item.cart_id,
            quantity=cart_item.quantity,
            product_id=cart_item.product_id,
            section_id=product.section_id
        )

        # Add the order to the database
        db.session.add(order)

    # Delete all cart items for the current user
    Cart.query.filter_by(user_id=user_id).delete()

    # Commit the changes to the database
    db.session.commit()

    # Show a flash message and redirect to the orders page
    flash('Purchase Successful! View History.', 'success')
    return redirect(url_for('orders'))



@app.route('/orders', endpoint='orders')
@login_required('user')
def orders():
    user_id = session['user_id']

    # Get all orders for the current user
    orders = Orders.query.filter_by(user_id=user_id).all()

    # Create a dictionary to store order details
    order_details = {}

    for order in orders:
        # Get the product and category details for each order
        product = Product.query.get(order.product_id)
        category = Category.query.get(product.section_id)

        # Create a tuple with product and category details
        order_info = (product.name, category.name, order.quantity, product.rate_per_unit, (order.quantity * product.rate_per_unit))

        # If the order_number already exists in the dictionary, append the order_info to the existing list
        if order.order_number in order_details:
            order_details[order.order_number].append(order_info)
        else:
            # If the order_number doesn't exist, create a new list with order_info
            order_details[order.order_number] = [order_info]

    return render_template('orders.html', orders=order_details)


@app.route('/add_to_cart_or_purchase', methods=['POST'], endpoint='add_to_cart_or_purchase')
@login_required('user')
def add_to_cart_or_purchase():
    user_id = session['user_id']
    product_ids = request.form.getlist('product_id')
    section_ids = request.form.getlist('section_id')
    quantity = request.form.get('quantity')
    action = request.form.get('action')

    for product_id, section_id in zip(product_ids, section_ids):
        if action == 'cart':
            # Create a new cart item record
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                section_id=section_id,
                quantity=quantity
            )

            # Add the cart item to the database
            db.session.add(cart_item)

        elif action == 'purchase':
            # Create a new order record
            order = Orders(
                user_id=user_id,
                product_id=product_id,
                section_id=section_id,
                quantity=quantity,
                order_number=Orders.query.filter_by(user_id=user_id).count() + 1
            )

            # Add the order to the database
            db.session.add(order)

    # Commit the changes to the database
    db.session.commit()

    if action == 'cart':
        flash('Item Added to Cart Successfully!', 'success')
        return redirect(url_for('user_dashboard'))
    elif action == 'purchase':
        flash('Successfully Purchased!', 'success')
        return redirect(url_for('orders'))

