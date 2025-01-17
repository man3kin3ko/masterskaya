from flask import Flask, request, redirect, render_template, make_response
from .config import Config
from .utils import cycle_list

from app.db import DBProxy
import app.db as db

app = Flask(__name__, static_folder="dist", static_url_path="")
db_proxy = DBProxy()
app.config["SQLALCHEMY_DATABASE_URI"] = db_proxy.engine
app.jinja_env.globals['config'] = Config
# app.jinja_env.globals['cached_categs'] = filter(lambda x: x[0].is_empty(), db_proxy.get_categories())

@app.template_filter()
def priceFormat(value):
    rev = str(value)[::-1]
    groups = [rev[i:i + 3] for i in range(0, len(rev), 3)]
    return ' '.join(groups)[::-1]

@app.route("/")
async def index():
    return render_template("index.html")

# @app.route("/store/cameras/")
# async def cameras_dbg():
#     cameras = [i[0] for i in db_proxy.get_resale_cameras()]
#     return render_template("cameras.html", cameras=cameras)

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
    session = db_proxy.create_session()
    order = db.repair_order_by_uuid(uuid)
    return render_template("tracking.html", order=order)

@app.route("/tracking/")
async def tracking():
    return render_template("tracking.html")

@app.route("/tracking")
async def trail():
    return redirect("/tracking/", code=302)

@app.route("/tracking/is_exist", methods=["POST"])
async def is_exist():
    session = db_proxy.create_session()
    if (db.is_repair_order_exist(session, request.data.decode("utf-8"))):
        return '', 200
    return '', 404

@app.route("/store/")
async def store():
    session = db_proxy.create_session()
    return render_template(
        "store.html", 
        categories=cycle_list(db.categories(session))
        )


@app.route("/store/cameras/")
async def cameras():
    return redirect("/error", code=302)


@app.route("/store/spares/")
async def spares():
    session = db_proxy.create_session()
    return render_template(
        "spares.html", 
        categories=db.categories(session)
        )


@app.route("/store/spares/<subtype>")
async def rest_spare_redirect(subtype):
    return redirect(f"/store/spares#{subtype}", code=302)


@app.route("/store/spares/<subtype>/<slug>/")
async def spare_details(subtype, slug):
    session = db_proxy.create_session()
    
    spares = db.spares_by_subtype_and_slug(session, subtype, slug)
    brands = [i.brand for i in spares]

    return render_template(
        "detail-store-page.html",
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