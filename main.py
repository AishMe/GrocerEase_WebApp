import os
from flask import Flask
from flask_restful import Api
from application import config
from application.config import LocalDevelopmentConfig
from application.database import db

app = None
api = None

def create_app():
	app = Flask(__name__, template_folder= "templates")
	if os.getenv('ENV', "development") == "production":
		raise Exception("Currently no production config is setup.")
	else:
		print("Starting Local Development")
		app.config.from_object(LocalDevelopmentConfig)

	db.init_app(app)
	api = Api(app)
	app.app_context().push()
	return app, api

app, api = create_app()

# Import all the controllers so they are loaded
from application.controllers import *
from application.api import UserAPI, ProductAPI, CategoryAPI

api.add_resource(UserAPI, '/api/users', '/api/users/<int:user_id>', '/api/users/<int:user_id>')
api.add_resource(ProductAPI, '/api/products', '/api/products/<int:product_id>', '/api/products/<int:product_id>')
api.add_resource(CategoryAPI, '/api/categories', '/api/categories/<int:section_id>', '/api/categories/<int:section_id>')

if __name__ =='__main__':
	# Run the Flask app
	app.run(host='0.0.0.0', port=8080)