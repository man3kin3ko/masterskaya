from flask import Flask, request, send_from_directory
from .db_models import db

app = Flask(__name__, static_folder="dist", static_url_path='')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"

@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'index.html')


app.app_context().push()
db.init_app(app)
db.create_all()