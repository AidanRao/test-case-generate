import atexit

from flask import Flask
from flask_cors import CORS

from app.config import AppConfig
from app.routes.projects import projects_bp
from app.routes.quality import quality_bp
from app.routes.requirements import requirements_bp
from app.routes.testcases import testcases_bp
from app.routes.ai_config import ai_config_bp
from app.routes.system_tasks import system_tasks_bp
from app.storage.json_storage import JsonStorage
from app.scheduler import SystemTaskManager
from app.services.testcase_job_manager import TestCaseJobManager


def create_app():
    app = Flask(__name__)
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
    )
    app_config = AppConfig()
    app.config["APP_CONFIG"] = app_config
    storage = JsonStorage(app_config.data_dir, app_config.uniportal_storage_path)
    app.config["STORAGE"] = storage

    testcase_job_manager = TestCaseJobManager(
        storage,
        app_config,
        max_workers=app_config.testcase_job_workers,
        max_history=app_config.testcase_job_history,
    )
    app.extensions["testcase_job_manager"] = testcase_job_manager
    atexit.register(testcase_job_manager.shutdown)

    system_task_manager = SystemTaskManager(storage.system_task_store, storage)
    system_task_manager.start()
    app.extensions["system_task_manager"] = system_task_manager

    app.register_blueprint(projects_bp, url_prefix="/v1")
    app.register_blueprint(requirements_bp, url_prefix="/v1")
    app.register_blueprint(testcases_bp, url_prefix="/v1")
    app.register_blueprint(quality_bp, url_prefix="/v1")
    app.register_blueprint(ai_config_bp, url_prefix="/v1")
    app.register_blueprint(system_tasks_bp, url_prefix="/v1")

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "ok"}, 200

    return app
