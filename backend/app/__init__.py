from flask import Flask, request
from .db_models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"
with app.app_context():
    db.init_app(app)
    db.create_all()