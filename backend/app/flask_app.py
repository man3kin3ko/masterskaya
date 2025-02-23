from flask import Flask, request, redirect, render_template, make_response
from .config import Config
from .utils import cycle_list

from app.db import DBProxy
import app.db as db

app = Flask(__name__, static_folder="dist", static_url_path="")
db_proxy = DBProxy()
app.config["SQLALCHEMY_DATABASE_URI"] = db_proxy.engine
app.jinja_env.globals['config'] = Config

session = db_proxy.create_session()
app.jinja_env.globals['cached_categs'] = db.categories(session)

@app.template_filter()
def priceFormat(value):
    rev = str(value)[::-1]
    groups = [rev[i:i + 3] for i in range(0, len(rev), 3)]
    return ' '.join(groups)[::-1]

@app.route("/")
async def index():
    return render_template("index.html")

@app.errorhandler(404)
async def page_not_found(e):
    return render_template("404.html")

@app.route("/store/cameras/<uuid>")
async def camera_page(uuid):
    #     cameras = [i[0] for i in db_proxy.get_resale_cameras()]
    #     return render_template("cameras.html", cameras=cameras)
    return render_template("camera-store-page.html")

@app.route("/rules")
@app.route("/rules/")
async def rules():
    return render_template("rules.html")

@app.route("/route")
@app.route("/route/")
async def route():
    return redirect("/store/#route", 302)

@app.route("/tracking/<uuid>")
@app.route("/tracking/<uuid>/")
async def tracking_order(uuid):
    session = db_proxy.create_session()
    order = db.repair_order_by_uuid(uuid)
    return render_template("tracking.html", order=order)

@app.route("/tracking")
@app.route("/tracking/")
async def tracking():
    return render_template("tracking.html")

@app.route("/tracking/is_exist", methods=["POST"])
async def is_exist():
    session = db_proxy.create_session()
    if (db.is_repair_order_exist(session, request.data.decode("utf-8"))):
        return '', 200
    return '', 404

@app.route("/store")
@app.route("/store/")
async def store():
    session = db_proxy.create_session()
    return render_template(
        "store.html", 
        categories=cycle_list(db.not_empty_categories(session)) # ограничивать список по длине чтобы не тормозило?
        )

@app.route("/store/spares")
@app.route("/store/spares/")
async def spares():
    session = db_proxy.create_session()
    categs = db.categories(session)

    print(categs)
    return render_template(
        "spares.html", 
        categories=categs
        )

@app.route("/store/spares/<subtype>")
@app.route("/store/spares/<subtype>/")
async def rest_spare_redirect(subtype):
    return redirect(f"/store/spares#{subtype}", code=302)


@app.route("/store/spares/<subtype>/<slug>")
@app.route("/store/spares/<subtype>/<slug>/")
async def spare_details(subtype, slug):
    session = db_proxy.create_session()
    category = db.category_by_slug(session, subtype, slug)
    spares = list(db.spares_by_subtype_and_slug(session, subtype, slug))
    brands = set([i.brand for i in spares])

    return render_template(
        "detail-store-page.html",
        category=category,
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