import flask
from .config import Const
from flask import Flask, request, redirect, render_template
from .db_models import db

app = Flask(__name__, static_folder="dist", static_url_path="")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"


@app.route("/")
def index():
    return render_template("index.html", config=Const)


@app.errorhandler(404)
def page_not_found(e):
    return "404", 404


@app.route("/store/")
def store():
    return render_template("store.html", config=Const)


@app.route("/store/cameras/")
def cameras():
    return render_template("base.html", config=Const)


@app.route("/store/spares/")
def spares():
    return render_template("spares.html", config=Const)


@app.route("/store/spares/mecha")
def rest_spare_mecha_redirect():
    return redirect("/store/spares#mecha", code=302)


@app.route("/store/spares/electrical")
def rest_spare_electrical_redirect():
    return redirect("/store/spares#electrical", code=302)

@app.route("/store/spares/mecha/<catalogue_section>/")
@app.route("/store/spares/electrical/<catalogue_section>/")
def electrical_details(catalogue_section):
    return render_template("detail-catalogue-page.html", config=Const)


app.app_context().push()
db.init_app(app)
db.create_all()
