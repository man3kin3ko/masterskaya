import click
import uuid
import logging
from .tg import start_bot_command
from flask import Flask, request, redirect, render_template, make_response, g
from .config import Config
from .utils import cycle_list
from .db import db_proxy, init_db, SpareType, dump_db, restore_db

app = Flask(__name__, static_folder="dist", static_url_path="")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
with app.app_context():
    db_proxy.assign_app(app)
    db_proxy.db.init_app(app)
    db_proxy.db.create_all()
    if 'db' not in g:
        g.db = db_proxy.db
        
app.jinja_env.globals['config'] = Config
app.jinja_env.globals['cached_categs'] = filter(lambda x: x[0].is_empty(), db_proxy.get_categories())

@app.route("/")
async def index():
    return render_template("index.html")

@app.errorhandler(404)
async def page_not_found(e):
    return render_template("404.html")

@app.route("/rules")
async def rules():
    return render_template("rules.html")

@app.route("/route")
async def route():
    return render_template("route.html")

@app.route("/tracking/<uuid>")
async def tracking_order(uuid):
    order = db_proxy.get_repair_order(uuid)
    return render_template("tracking.html", order=order)

@app.route("/tracking/")
async def tracking():
    return render_template("tracking.html")

@app.route("/tracking")
async def trail():
    return redirect("/tracking/", code=302)

@app.route("/tracking/is_exist", methods=["POST"])
async def is_exists():
    if (db_proxy.is_repair_order_exist(request.data.decode("utf-8"))):
        return '', 200
    return '', 404

@app.route("/store/")
async def store():
    categories = db_proxy.get_categories()
    return render_template(
        "store.html", 
        categs=cycle_list(list(
            filter(lambda x: x[0].is_empty(), categories)
            )
        ))


@app.route("/store/cameras/")
async def cameras():
    return redirect("/error", code=302)


@app.route("/store/spares/")
async def spares():
    categories = db_proxy.get_categories()
    return render_template(
        "spares.html", 
        categs=filter(
            lambda x: x[0].is_empty(), categories
            ))


@app.route("/store/spares/mecha")
async def rest_spare_mecha_redirect():
    return redirect("/store/spares#mecha", code=302)


@app.route("/store/spares/electrical")
async def rest_spare_electrical_redirect():
    return redirect("/store/spares#electrical", code=302)

@app.route("/store/spares/<spare_type>/<spare_category>/")
async def electrical_details(spare_type, spare_category):
    spare_type = SpareType(spare_type)
    spare_category = db_proxy.get_category_by_name(spare_category)
    spares, brands = db_proxy.get_spares_by_category_and_type(spare_type.name, spare_category.prog_name)

    return render_template(
        "detail-catalogue-page.html",
        spare_type=spare_type,
        spare_category=spare_category,
        spares=spares,
        brands=brands
    )

@app.route("/sitemap")
@app.route("/sitemap/")
@app.route("/sitemap.xml")
def sitemap():
    sitemap = render_template("sitemap.xml", urls=map(
        lambda x: f"https://{Config.HOSTNAME}{x}",
    [
        "/",
        "/route",
        "/store",
        "/store/cameras/",
        "/store/spares/",
        "/store/spares/mecha",
        "/store/spares/electrical"
    ]))
    response = make_response(sitemap)
    response.headers["Content-Type"] = "application/xml"

    return response

# todo: move cli commands

@click.command("init-db")
def init_db_command():
    with app.app_context():
        init_db(db_proxy.db)

@click.command("dump-db")
def dump_db_command():
    with app.app_context():
        dump_db(db_proxy.db)

@click.command("restore-db")
def restore_db_command():
    with app.app_context():
        restore_db(db_proxy.db)

app.cli.add_command(init_db_command)
app.cli.add_command(start_bot_command)
app.cli.add_command(dump_db_command)
app.cli.add_command(restore_db_command)