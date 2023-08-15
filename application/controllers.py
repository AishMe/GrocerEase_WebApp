from flask import Flask, session, request, redirect, render_template, url_for, flash
from flask import current_app as app
from .database import db
from application.models import User, Category, Product, Cart, Orders
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from datetime import date
import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
import io
import base64


app.config['SECRET_KEY'] = "harekrishna"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.sqlite3'


# Create a Search Form
class SearchForm(FlaskForm):
    searched = StringField("Searched")
    section_id = StringField("Section ID")
    rate_sort = StringField("Rate Sorting")
    submit = SubmitField("Submit")

# Create a Filter Form
class FilterForm(FlaskForm):
    section_id = SelectField("Categories")
    rate_min = FloatField("Min Rate per Unit")
    rate_max = FloatField("Max Rate per Unit")
    date_order = SelectField("Manufacturing Date Order", choices=[('asc', 'Ascending'), ('desc', 'Descending')])
    submit = SubmitField("Apply Filter")


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
    cat_name = StringField("Enter the Category Name", validators=[DataRequired()])
    cat_image = StringField("Category Image")
    submit = SubmitField("Submit")


# Create a Product Form
class ProductForm(FlaskForm):
    product_name = StringField("Product Name", validators=[DataRequired()])
    rate = StringField("Rate", validators=[DataRequired()])
    stock = StringField("Stock", validators=[DataRequired()])
    unit = StringField("Unit", validators=[DataRequired()])
    image = StringField("Image")
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


@app.route('/')
def index():
    return render_template('index.html')


# Create Custom Error Pages

# Invalid Page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error404.html'), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template('error500.html'), 500


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

    today = date.today()
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
                           currentYear=today.year, 
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

    return render_template('user_dashboard.html', categories=categories, products_by_category=products_by_category)

# Add Category
@app.route('/add_category', methods=['GET', 'POST'], endpoint="add_category")
@login_required(role='manager')
def add_category():
    name = None
    form = CategoryForm()

    if form.validate_on_submit():
        category = Category.query.filter_by(name=form.cat_name.data).first()
        if category is None:
            category = Category(name=form.cat_name.data, 
                                cat_image=form.cat_image.data)
            
            db.session.add(category)
            db.session.commit()

        name = form.cat_name.data
        form.cat_name.data = ''
        form.cat_image.data = ''

        flash('Category Added Successfully!')
        return redirect(url_for('manager_dashboard'))

    all_categories = Category.query.order_by(Category.section_id)
    return render_template('add_category.html', 
                           form=form, 
                           name=name, 
                           all_categories=all_categories)


# Update Database Record in Category
@app.route('/update_category/<int:section_id>', methods=['GET', 'POST'], endpoint="update_category")
@login_required(role='manager')
def update_category(section_id):
    category_to_update = Category.query.get_or_404(section_id)
    form = CategoryForm()

    if form.validate_on_submit():
        category_to_update.name = form.cat_name.data
        category_to_update.cat_image = form.cat_image.data

        db.session.add(category_to_update)
        db.session.commit()

        flash("Category Information Has Been Updated!")
        return redirect(url_for('manager_dashboard', section_id=section_id))
    
    form.cat_name.data = category_to_update.name
    form.cat_image.data = category_to_update.cat_image

    return render_template('add_category.html', form=form)


# Delete a Category from the Database Record
@app.route('/delete_category/<int:section_id>', endpoint="delete_category")
@login_required(role='manager')
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

        product = Product(
            name=form.product_name.data,
            rate_per_unit=form.rate.data,
            stock=form.stock.data,
            unit=form.unit.data, 
            image=form.image.data,
            manufacture_date = datetime.today().strftime('%d-%m-%y'), 
            section_id = section_id
        )

        db.session.add(product)
        db.session.commit()

        form.product_name.data = ''
        form.rate.data = ''
        form.stock.data = ''
        form.unit.data = ''
        form.image.data = ''

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
        product_to_update.image = form.image.data

        db.session.add(product_to_update)
        db.session.commit()

        flash("Product Information Has Been Updated!")
        return redirect(url_for('manager_dashboard', product_id=product_id))
    
    form.product_name.data = product_to_update.name
    form.rate.data = product_to_update.rate_per_unit
    form.unit.data = product_to_update.unit
    form.stock.data = product_to_update.stock
    form.image.data = product_to_update.image

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
            flash("You Are Logged In As User!!")
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


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


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
            'image': product.image, 
            'cart_id': cart.cart_id
        })

    # Calculate overall total price
    total_price = sum(item['total_price'] for item in cart_data)

    return render_template('cart.html', cart_data=cart_data, total_price=total_price)


@app.route('/remove_from_cart', methods=['POST'], endpoint='remove_from_cart')
@login_required('user')
def remove_from_cart():
    cart_id = request.form.get('cart_id')
    cart_item = Cart.query.get(cart_id)

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'success')
    else:
        flash('Failed to remove item from cart.', 'danger')

    return redirect(url_for('cart'))


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

    total_price = 0
    # Create new order records for each cart item and calculate total_price
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)

        # Calculate total_price
        total_price += product.rate_per_unit * cart_item.quantity

    # Update stock values and create order records
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        
        # Ensure that the purchased quantity is not greater than the available stock
        if cart_item.quantity <= product.stock:
            # Create a new order record
            order = Orders(
                order_number=current_order_number,
                user_id=user_id,
                cart_id=cart_item.cart_id,
                quantity=cart_item.quantity,
                product_id=cart_item.product_id,
                section_id=product.section_id, 
                total_price=total_price
            )

            # Subtract the purchased quantity from the product's stock
            product.stock -= cart_item.quantity

            # Add the order to the database
            db.session.add(order)

            # Update the product's stock in the database
            db.session.commit()

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
    order_total_prices = {}

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

        order_total_prices[order.order_number] = order.total_price

    return render_template('orders.html', orders=order_details, order_total_prices=order_total_prices)



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


@app.route('/delete_cart_item', methods=['POST'], endpoint='delete_cart_item')
@login_required('user')
def delete_cart_item():
    user_id = session['user_id']
    product_id = request.form.get('product_id')

    # Get the cart item for the current user and product
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        # Delete the cart item from the database
        db.session.delete(cart_item)
        db.session.commit()

        flash('Item deleted from cart successfully!', 'success')
    else:
        flash('Cart item not found!', 'danger')

    return redirect(url_for('cart'))


@app.route('/manager/summary', endpoint='manager_summary')
@login_required(role='manager')
def manager_summary():
    # Fetch additional data for the summary card
    user_count = User.query.filter(User.is_manager == 0).count()
    avg_money_spent = calculate_average_money_spent()
    out_of_stock_count = calculate_out_of_stock_items()
    least_of_stock = calculate_least_of_stock_items()

    # Fetch data from the database
    categories = Category.query.all()
    category_names = [category.name for category in categories]
    category_counts = []

    for category in categories:
        count = db.session.query(db.func.count(Product.product_id)).filter(Product.section_id == category.section_id).scalar()
        category_counts.append(count)

    # Create graphs
    # Bar chart: Products by Category
    plt.figure(figsize=(10, 5))
    plt.bar(category_names, category_counts)
    plt.xlabel('Category')
    plt.ylabel('Number of Products')
    plt.title('Products by Category')
    bar_chart_image = get_image_base64()

    # Pie chart: Top Selling Products
    top_products = db.session.query(Product.name, db.func.sum(Orders.quantity).label('total_quantity')).\
        join(Orders, Product.product_id == Orders.product_id).\
        group_by(Product.name).order_by(db.desc('total_quantity')).limit(5).all()

    top_product_names = [product[0] for product in top_products]
    top_product_quantities = [product[1] for product in top_products]

    plt.figure(figsize=(8, 8))
    plt.pie(top_product_quantities, labels=top_product_names, autopct='%1.1f%%')
    plt.title('Top Selling Products')
    pie_chart_image = get_image_base64()

    # Advanced: Correlation between Quantity and Price
    products = Product.query.all()
    quantities = [product.stock for product in products]
    prices = [product.rate_per_unit for product in products]

    plt.figure(figsize=(8, 6))
    plt.scatter(quantities, prices, color='b', alpha=0.5)
    plt.xlabel('Quantity in Stock')
    plt.ylabel('Price per Unit ($)')
    plt.title('Correlation between Quantity and Price')
    plt.grid(True)
    correlation_image = get_image_base64()

    # Advanced: Sales Distribution by Category
    sales_by_category = db.session.query(Category.name, db.func.sum(Orders.quantity * Product.rate_per_unit).label('total_sales')).\
        join(Product, Category.section_id == Product.section_id).\
        join(Orders, Product.product_id == Orders.product_id).\
        group_by(Category.name).order_by(db.desc('total_sales')).all()

    category_names = [category[0] for category in sales_by_category]
    total_sales_per_category = [category[1] for category in sales_by_category]

    plt.figure(figsize=(10, 5))
    plt.bar(category_names, total_sales_per_category)
    plt.xlabel('Category')
    plt.ylabel('Total Sales ($)')
    plt.title('Sales Distribution by Category')
    plt.xticks(rotation=45)
    sales_distribution_image = get_image_base64()

    # Item Distribution chart
    # Fetch item distribution data from the database and create the chart
    item_distribution_data = db.session.query(Product.name, Product.stock).all()
    item_names = [item[0] for item in item_distribution_data]
    item_quantities = [item[1] for item in item_distribution_data]

    plt.figure(figsize=(10, 5))
    plt.bar(item_names, item_quantities)
    plt.xlabel('Item')
    plt.ylabel('Quantity in Stock')
    plt.title('Item Distribution')
    plt.xticks(rotation=45)
    item_distribution_image = get_image_base64()

    return render_template('summary.html',
                           correlation_image=correlation_image,
                           sales_distribution_image=sales_distribution_image,
                           bar_chart_image=bar_chart_image,
                           pie_chart_image=pie_chart_image,
                           item_distribution_image=item_distribution_image,
                           user_count=user_count,
                           avg_money_spent=avg_money_spent,
                           out_of_stock_count=out_of_stock_count,
                           least_of_stock=least_of_stock)


def calculate_average_money_spent():
    # Calculate the average money spent per user (excluding managers)
    subquery = db.session.query(db.func.sum(Orders.total_price).label('total_spent')).\
        join(User, User.user_id == Orders.user_id).\
        filter(User.is_manager == 0).\
        group_by(Orders.user_id).subquery()

    average_money_spent = db.session.query(db.func.avg(subquery.c.total_spent)).scalar()

    return round(average_money_spent, 2)


def calculate_out_of_stock_items():
    # Find products that are out of stock
    out_of_stock_products = Product.query.filter(Product.stock == 0).all()
    #out_of_stock_item_names = [product.name for product in out_of_stock_products]
    return len(out_of_stock_products)


def calculate_least_of_stock_items():
    # Get the least in stock products
    least_of_stock = db.session.query(Product, Category, Product.stock).\
        join(Category, Product.section_id == Category.section_id).\
        order_by(Product.stock).filter(Product.stock <= 50).all()

    return len(least_of_stock)

def get_image_base64():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    return image_base64



@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


@app.route('/manager_search', methods=['GET', 'POST'])
def manager_search():
    form = SearchForm()
    sections = Category.query.all()

    if request.method == 'POST' and form.validate_on_submit():
        products_searched = form.searched.data
        products = Product.query.filter(Product.name.like('%' + products_searched + '%')).all()
    else:
        products_searched = None
        products = Product.query.all()

    return render_template('manager_search.html', form=form, searched=products_searched, products=products, sections=sections)


@app.route('/manager_apply_filter', methods=['POST'])
def manager_apply_filter():
    form = SearchForm(request.form)

    sections = Category.query.all()
    products = Product.query

    section_id = form.section_id.data
    rate_sort = form.rate_sort.data
    min_rate = float(request.form.get('min_rate', 0))
    max_rate = float(request.form.get('max_rate', 10000))
    manufacture_date_order = request.form.get('manufacture_date_order')
    stock_order = request.form.get('stock_order')

    if section_id:
        products = products.filter(Product.section_id == section_id)

    if rate_sort == 'asc':
        products = products.order_by(Product.rate_per_unit.asc())
    elif rate_sort == 'desc':
        products = products.order_by(Product.rate_per_unit.desc())

    products = products.filter(Product.rate_per_unit.between(min_rate, max_rate))

    if manufacture_date_order == 'newest':
        products = products.order_by(Product.manufacture_date.desc())
    elif manufacture_date_order == 'oldest':
        products = products.order_by(Product.manufacture_date.asc())

    if stock_order == 'least':
        products = products.order_by(Product.stock.asc())
    elif stock_order == 'highest':
        products = products.order_by(Product.stock.desc())

    products = products.all()
    total_products = Product.query.count()

    return render_template('manager_search.html', form=form, products=products, sections=sections, total_products=total_products)

@app.route('/user_search', methods=['GET', 'POST'])
def user_search():
    form = SearchForm()
    sections = Category.query.all()

    if request.method == 'POST' and form.validate_on_submit():
        products_searched = form.searched.data
        products = Product.query.filter(Product.name.like('%' + products_searched + '%')).all()
    else:
        products_searched = None
        products = Product.query.all()

    return render_template('user_search.html', form=form, searched=products_searched, products=products, sections=sections)


@app.route('/user_apply_filter', methods=['POST'])
def user_apply_filter():
    form = SearchForm(request.form)

    sections = Category.query.all()
    products = Product.query

    section_id = form.section_id.data
    rate_sort = form.rate_sort.data
    min_rate = float(request.form.get('min_rate', 0))
    max_rate = float(request.form.get('max_rate', 10000))
    manufacture_date_order = request.form.get('manufacture_date_order')

    if section_id:
        products = products.filter(Product.section_id == section_id)

    if rate_sort == 'asc':
        products = products.order_by(Product.rate_per_unit.asc())
    elif rate_sort == 'desc':
        products = products.order_by(Product.rate_per_unit.desc())

    products = products.filter(Product.rate_per_unit.between(min_rate, max_rate))

    if manufacture_date_order == 'newest':
        products = products.order_by(Product.manufacture_date.desc())
    elif manufacture_date_order == 'oldest':
        products = products.order_by(Product.manufacture_date.asc())

    products = products.all()
    total_products = Product.query.count()

    return render_template('user_search.html', form=form, products=products, sections=sections, total_products=total_products)