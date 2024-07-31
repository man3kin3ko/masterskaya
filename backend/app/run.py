import click
import uuid
import logging

from app.telegram_bridge import bot
from flask import Flask, request, redirect, render_template
from app.config import Config
from app.utils import cycle_list
import app.db_models as db

app = Flask(__name__, static_folder="dist", static_url_path="")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

with app.app_context():
    instance = db.get_db()
    instance.init_app(app)
    instance.create_all()


@app.route("/")
def index():
    return render_template("index.html", config=Config)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", config=Config)

@app.route("/tracking")
def tracking():
    return render_template("tracking.html", config=Config)


@app.route("/store/")
def store():
    return render_template("store.html", config=Config, categs=cycle_list(db.get_categs()))


@app.route("/store/cameras/")
def cameras():
    return redirect("/error", code=302)


@app.route("/store/spares/")
def spares():
    return render_template("spares.html", config=Config, categs=db.get_categs())


@app.route("/store/spares/mecha")
def rest_spare_mecha_redirect():
    return redirect("/store/spares#mecha", code=302)


@app.route("/store/spares/electrical")
def rest_spare_electrical_redirect():
    return redirect("/store/spares#electrical", code=302)


@app.route("/form", methods=["POST"])
async def read_item():
    try:
        new_order_uuid = str(uuid.uuid4())
        db.save_repair_order(order_form, new_order_uuid)

        await bot.send_new_order(order_form, new_order_uuid)

        return {}, 200
    except Exception as e:
        return {e.__repr__()}, 500 # change later :3


@app.route("/store/spares/mecha/<spare_category>/")
@app.route("/store/spares/electrical/<spare_category>/")
def electrical_details(spare_category):
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
