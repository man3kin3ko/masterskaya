import click
import uuid
from .telegram_bridge import TelegramBridge, start_bot_command
from flask import Flask, request, redirect, render_template, g
from .config import Config
from .utils import cycle_list
from .db_models import db_proxy

app = Flask(__name__, static_folder="dist", static_url_path="")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
with app.app_context():
    db_proxy.assign_app(app)
    db_proxy.db.init_app(app)
    db_proxy.db.create_all()
    if 'db' not in g:
        g.db = db_proxy.db

@app.route("/")
async def index():
    return render_template("index.html", config=Config)

@app.errorhandler(404)
async def page_not_found(e):
    return render_template("404.html", config=Config)

@app.route("/tracking/<uuid>")
async def tracking_order(uuid):
    return render_template("tracking.html", config=Config, order=db.get_repair_order(db.OrderUUID(uuid=uuid).uuid))

@app.route("/tracking/")
async def tracking():
    return render_template("tracking.html", config=Config)

@app.route("/tracking")
async def trail():
    return redirect("/tracking/", code=302)

@app.route("/tracking/is_exist", methods=["POST"])
async def is_exists():
    uuid = db.OrderUUID(uuid=request.data.decode("utf-8")).uuid
    if (db.is_repair_order_exists(uuid)):
        return '', 200
    return '', 404

@app.route("/store/")
async def store():
    return render_template("store.html", config=Config, categs=cycle_list(db.get_categs()))


@app.route("/store/cameras/")
async def cameras():
    return redirect("/error", code=302)


@app.route("/store/spares/")
async def spares():
    return render_template("spares.html", config=Config, categs=db.get_categs())


@app.route("/store/spares/mecha")
async def rest_spare_mecha_redirect():
    return redirect("/store/spares#mecha", code=302)


@app.route("/store/spares/electrical")
async def rest_spare_electrical_redirect():
    return redirect("/store/spares#electrical", code=302)


@app.route("/store/spares/mecha/<spare_category>/")
@app.route("/store/spares/electrical/<spare_category>/")
async def electrical_details(spare_category):
    spare_type = "MECHA" if request.path.split("/")[3] == 'mecha' else "ELECTRIC"
    return render_template(
        "detail-catalogue-page.html",
        config=Config,
        spare_type=request.path.split("/")[3],
        human_spare_type="Механика" if request.path.split("/")[3] == 'mecha' else "Электроника",
        human_spare_category=db.get_human_name(spare_category),
        spares=db.get_spares(spare_type, spare_category),
        brands=db.get_brands(spare_type, spare_category),
    )


@click.command("init-db")
def init_db_command():
    with app.app_context():
        db.init_db()

app.cli.add_command(init_db_command)
app.cli.add_command(start_bot_command)