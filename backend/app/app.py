from flask import Flask, redirect, render_template
from .config import Config
from .utils import cycle_list
from sqlalchemy import insert
from .db_models import db, Brand, Spare, SpareCategory

app = Flask(__name__, static_folder="dist", static_url_path="")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"


@app.route("/")
def index():
    return render_template("index.html", config=Config)


@app.errorhandler(404)
def page_not_found(e):
    return "404", 404


@app.route("/store/")
def store():
    return render_template("store.html", config=Config, categs=cycle_list())


@app.route("/store/cameras/")
def cameras():
    return render_template("base.html", config=Config)


@app.route("/store/spares/")
def spares():
    return render_template("spares.html", config=Config, categs=None)


@app.route("/store/spares/mecha")
def rest_spare_mecha_redirect():
    return redirect("/store/spares#mecha", code=302)


@app.route("/store/spares/electrical")
def rest_spare_electrical_redirect():
    return redirect("/store/spares#electrical", code=302)

@app.route("/store/spares/mecha/<spare_category>/")
@app.route("/store/spares/electrical/<spare_category>/")
def electrical_details(spare_category):
    return render_template("detail-catalogue-page.html", config=Config, spares=None)


if __name__ == '__main__':
    with app.app_context():
        db.init_app(app)
        db.create_all()
        db.session.execute(
            insert(Brand),
            [
                {"name":"Codak", "country":"US"},
                {"name":"Canon", "country":"JP"},
                {"name":"Fujifilm", "country":"JP"},
                {"name":"Nikon", "country":"JP"},
                {"name":"Sony", "country":"JP"},
                {"name":"Olympus", "country":"JP"},
                {"name":"Panasonic", "country":"JP"},
                {"name":"Arsenal", "country":"SU"},
                {"name":"KMZ", "country":"SU"},
                {"name":"Lomo", "country":"SU"},
                {"name":"Zeiss", "country":"DE"},
                {"name":"Exacta", "country":"DE"},
                {"name":"Rolleiflex", "country":"DE"},
                {"name":"Balda", "country":"DE"},
                {"name":"Welta", "country":"DE"},
                {"name":"Agfa", "country":"DE"},
            ],
        )
        db.session.execute(
            insert(SpareCategory),
            [
                {"name":"Затворы","type":"mecha","description":"хуйхуйхуйхуйхуй","image_name":"3b71160fc60290752cb7.jpg","prog_name":"shutter"},
                {"name":"Затворы","type":"electrical","description":"хуйхуйхуйхуйхуй","image_name":"3b71160fc60290752cb7.jpg","prog_name":"shutter"},
                {"name":"Матрицы","type":"electrical","description":"хуйхуйхуйхуйхуй","image_name":"3b71160fc60290752cb7.jpg","prog_name":"matrices"},
                {"name":"Шлейфы","type":"electrical","description":"хуйхуйхуйхуйхуй","image_name":"3b71160fc60290752cb7.jpg","prog_name":"stubs"},
            ],
        )
        db.session.execute(
            insert(Spare),
            [
                {"brand_id":2, "categ_id":3,"name":"Digital IXUS 132/IXUS 135","price":600, "quantity":3},
                {"brand_id":2,"categ_id":3,"name":"EOS 1D Mark III","price":4900, "quantity":3},
                {"brand_id":2,"categ_id":3,"name":"PowerShot A2300/A2400","price":500, "quantity":3},

            ]
        )
        db.session.commit()

app.run()