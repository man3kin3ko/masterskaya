from .utils import cycle_list
from .config import Config
from flask import Flask, request, redirect, render_template
from .db_models import db, test_categs, test_spares

app = Flask(__name__, static_folder="dist", static_url_path="")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"


@app.route("/")
def index():
    return render_template("index.html", config=Config)


@app.errorhandler(404)
def page_not_found(e):
    return "404", 404


@app.route("/store/")
def store():
    return render_template("store.html", config=Config, categs=cycle_list(test_categs*3))


@app.route("/store/cameras/")
def cameras():
    return render_template("base.html", config=Config)


@app.route("/store/spares/")
def spares():
    return render_template("spares.html", config=Config, categs=test_categs*3)


@app.route("/store/spares/mecha")
def rest_spare_mecha_redirect():
    return redirect("/store/spares#mecha", code=302)


@app.route("/store/spares/electrical")
def rest_spare_electrical_redirect():
    return redirect("/store/spares#electrical", code=302)

@app.route("/store/spares/mecha/<spare_category>/")
@app.route("/store/spares/electrical/<spare_category>/")
def electrical_details(spare_category):
    return render_template("detail-catalogue-page.html", config=Config, spares=test_spares)


app.app_context().push()
db.init_app(app)
db.create_all()
