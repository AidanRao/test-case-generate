from flask import Flask
from threading import Lock
from flask_cors import CORS

from app.config import AppConfig
from app.routes.projects import projects_bp
from app.routes.quality import quality_bp
from app.routes.requirements import requirements_bp
from app.routes.testcases import testcases_bp
from app.routes.ai_config import ai_config_bp
from app.routes.system_tasks import system_tasks_bp
from app.storage.json_storage import JsonStorage


def create_app():
    app = Flask(__name__)
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
    )
    app_config = AppConfig()
    app.config["APP_CONFIG"] = app_config
    storage = JsonStorage(
        app_config.data_dir,
        app_config.uniportal_storage_path,
        app_config.uniportal_sync_enabled,
        app_config.uniportal_sync_interval_seconds,
    )
    app.config["STORAGE"] = storage
    app.config["TESTCASE_JOBS"] = {"lock": Lock(), "jobs": {}}

    app.register_blueprint(projects_bp, url_prefix="/v1")
    app.register_blueprint(requirements_bp, url_prefix="/v1")
    app.register_blueprint(testcases_bp, url_prefix="/v1")
    app.register_blueprint(quality_bp, url_prefix="/v1")
    app.register_blueprint(ai_config_bp, url_prefix="/v1")
    app.register_blueprint(system_tasks_bp, url_prefix="/v1")

    return app
