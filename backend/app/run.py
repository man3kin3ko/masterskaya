import click
from flask import Flask, request, redirect, render_template
from app.config import Config
from app.utils import cycle_list
from sqlalchemy import insert
from app.db_models import get_db, get_spares, get_brands, get_categs, get_human_name, Brand, Spare, SpareCategory

app = Flask(__name__, static_folder="dist", static_url_path="")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

with app.app_context():
    db = get_db()
    db.init_app(app)
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html", config=Config)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", config=Config)


@app.route("/store/")
def store():
    return render_template("store.html", config=Config, categs=cycle_list(get_categs()))


@app.route("/store/cameras/")
def cameras():
    return render_template("base.html", config=Config)


@app.route("/store/spares/")
def spares():
    return render_template("spares.html", config=Config, categs=get_categs())


@app.route("/store/spares/mecha")
def rest_spare_mecha_redirect():
    return redirect("/store/spares#mecha", code=302)


@app.route("/store/spares/electrical")
def rest_spare_electrical_redirect():
    return redirect("/store/spares#electrical", code=302)


@app.route("/store/spares/mecha/<spare_category>/")
@app.route("/store/spares/electrical/<spare_category>/")
def electrical_details(spare_category):
    spare_type = "MECHA" if request.path.split("/")[3] == 'mecha' else "ELECTRIC"
    return render_template(
        "detail-catalogue-page.html",
        config=Config,
        spare_type=request.path.split("/")[3],
        human_spare_type="Механика" if request.path.split("/")[3] == 'mecha' else "Электроника",
        human_spare_category=get_human_name(spare_category),
        spares=get_spares(spare_type, spare_category),
        brands=get_brands(spare_type, spare_category),
    )


@click.command("init-db")
def init_db_command():
    with app.app_context():
        db.session.execute(
            insert(Brand),
            [
                {"name": "Kodak", "country": "US"},
                {"name": "Canon", "country": "JP"},
                {"name": "Fujifilm", "country": "JP"},
                {"name": "Nikon", "country": "JP"},
                {"name": "Sony", "country": "JP"},
                {"name": "Sigma", "country": "JP"},
                {"name": "Pentax", "country": "JP"},
                {"name": "Olympus", "country": "JP"},
                {"name": "Panasonic", "country": "JP"},
                {"name": "Samsung", "country": "KR"},
                {"name": "Arsenal", "country": "SU"},
                {"name": "KMZ", "country": "SU"},
                {"name": "Lomo", "country": "SU"},
                {"name": "Zeiss", "country": "DE"},
                {"name": "Exacta", "country": "DE"},
                {"name": "Rolleiflex", "country": "DE"},
                {"name": "Balda", "country": "DE"},
                {"name": "Welta", "country": "DE"},
                {"name": "Agfa", "country": "DE"},
            ],
        )
        db.session.execute(
            insert(SpareCategory),
            [
                {
                    "name": "Затворы",
                    "type": "MECHA",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "test_categ1.png",
                    "prog_name": "shutter",
                },
                {
                    "name": "Затворы",
                    "type": "ELECTRIC",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "test_categ2.png",
                    "prog_name": "shutter",
                },
                {
                    "name": "Матрицы",
                    "type": "ELECTRIC",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "matrices",
                },
                {
                    "name": "Шлейфы",
                    "type": "ELECTRIC",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "stubs",
                },
                                {
                    "name": "Платы",
                    "type": "ELECTRIC",
                    "description": "хуйхуйхуйхуйхуй",
                    "image_name": "3b71160fc60290752cb7.jpg",
                    "prog_name": "stubs",
                },
            ],
        )
        db.session.execute(
            insert(Spare),
            [
                {
                    "brand_id": 2,
                    "categ_id": 3,
                    "name": "Digital IXUS 132/IXUS 135",
                    "price": 600,
                    "quantity": 3,
                },
                {
                    "brand_id": 2,
                    "categ_id": 3,
                    "name": "EOS 1D Mark III",
                    "price": 4900,
                    "quantity": 3,
                },
                {
                    "brand_id": 2,
                    "categ_id": 3,
                    "name": "PowerShot A2300/A2400",
                    "price": 500,
                    "quantity": 3,
                },
            ],
        )
        db.session.commit()


app.cli.add_command(init_db_command)
