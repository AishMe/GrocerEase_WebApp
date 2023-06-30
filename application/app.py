from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from models import User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.sqlite3'
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manager_login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username exists in the database
        user = User.query.filter_by(username=username, role='Manager').first()
        if not user:
            return "Please try again. Username not found!"
        
        # Check if password matches
        if user.password != password:
            return "Please try again. Password is wrong!"

        # Successful login, redirect to manager dashboard
        return redirect('/manager_dashboard')

    return render_template('manager_login.html')


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


@app.route('/manager_dashboard')
def manager_dashboard():
    # Fetch manager's name from the database
    manager_username = "manager1"  # Replace with the logged-in manager's username
    manager = User.query.filter_by(username=manager_username, role='Manager').first()

    if manager:
        manager_name = manager.name
    else:
        manager_name = "Unknown Manager"

    return render_template('manager_dashboard.html', name=manager_name)


@app.route('/user_dashboard')
def user_dashboard():
    # Fetch user's name from the database
    user_username = "user1"  # Replace with the logged-in user's username
    user = User.query.filter_by(username=user_username, role='User').first()

    if user:
        user_name = user.name
    else:
        user_name = "Unknown User"

    return render_template('user_dashboard.html', name=user_name)

if __name__ == '__main__':
    app.run(debug=True)








'''
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def starting_page():
    return render_template('starting_page.html')

@app.route('/manager_dashboard')
def manager_dashboard():
    name = "John Doe"  # Replace with the actual manager's name
    return render_template('manager_dashboard.html', name=name)

@app.route('/user_dashboard')
def user_dashboard():
    name = "Jane Smith"  # Replace with the actual user's name
    return render_template('user_dashboard.html', name=name)

if __name__ == '__main__':
    app.run(debug=True)
'''
