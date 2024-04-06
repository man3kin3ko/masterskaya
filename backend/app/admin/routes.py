from flask import Blueprint
from ..utils import admin_only

admin = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")