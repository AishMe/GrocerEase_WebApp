from flask import Flask, request, redirect, render_template, url_for, flash
from flask import current_app as app
from .database import db
from application.models import User, Posts
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import TextArea
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user


app.config['SECRET_KEY'] = "harekrishna"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.sqlite3'


# Flask-Login Stuffs
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def login_user(user_id):
    return User.query.get(user_id)

# Create a Posts Form
class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    author = StringField("Author", validators=[DataRequired()])
    slug = StringField("Slug", validators=[DataRequired()])
    submit = SubmitField("Submit")

# Create a Form Class
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password_hash = PasswordField("Password", validators=[DataRequired(), EqualTo('password_hash_confirm', message='Both Passwords must Match!')])
    password_hash_confirm = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a Namer Form
class PasswordForm(FlaskForm):
    email = StringField("Enter Email ID", validators=[DataRequired()])
    password_hash = PasswordField("Enter password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a Namer Form
class NamerForm(FlaskForm):
    name = StringField("What's your name?", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a Login Form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


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


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username exists in the database
        user = User.query.filter_by(username=username, role='User').first()
        if not user:
            return "No such username exists. Register here"

        # Check if password matches
        if user.password != password:
            return "The password entered is wrong. Please try again!"

        # Successful login, redirect to user dashboard
        return redirect('/user_dashboard')

    return render_template('user_login.html')


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
            user = User(username=form.username.data, name=form.name.data, email=form.email.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data = ''
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
    
@app.route('/add-post', methods=['GET', 'POST'])
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        post = Posts(title=form.title.data, content=form.content.data, author=form.author.data)

        # Clear the Form
        form.title.data = ''
        form.content.data = ''
        form.author.data = ''
        form.slug.data = ''

        # Add post data to the database
        db.session.add(post)
        db.session.commit()

        # Return a Message
        flash('Blog Post Submitted Successfully!')

    # Redirect to the webpage
    return render_template('add_post.html', form=form)

# Show the Posts
@app.route('/posts')
def posts():
    # Grab all the posts from the database
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template('posts.html', posts=posts)

# Show Individual Post
@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)

# Edit the Post
@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()

    if form.validate_on_submit():
        
        post.title = form.title.data
        post.content = form.content.data
        post.author = form.author.data
        post.slug = form.slug.data

        # Update the Database
        db.session.add(post)
        db.session.commit()
        flash('Post Has Been Updated!')

        return redirect(url_for('post', id=post.id))
    
    form.title.data = post.title
    form.content.data = post.content
    form.author.data = post.author
    form.slug.data = post.slug

    return render_template('edit_post.html', form=form)

# Delete the Post
@app.route('/posts/delete/<int:id>')
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)

    try:
        db.session.delete(post_to_delete)
        db.session.commit()

        # Return a Message
        flash("Blog Post Deleted Successfully!")

        # Grab all the posts from the database
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template('posts.html', posts=posts)

    except:
        # Return an Error Message
        flash("Woops! There was an Problem. Pl Try Again")

        # Grab all the posts from the database
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template('posts.html', posts=posts)
    
# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            # Check the Hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successful!!")
                return redirect(url_for('dashboard'))
            
            else:
                flash('Oops..Wrong Password! Try Again...')

        else:
            flash("That User Doesn't Exist, Try Again...")
    return render_template('login.html', form=form)

# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


