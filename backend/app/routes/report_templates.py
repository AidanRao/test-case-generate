from flask import Blueprint, current_app

from app.reports.template_registry import available_templates
from app.utils.responses import ok


report_templates_bp = Blueprint("report_templates", __name__)


@report_templates_bp.get("/testcase-report-templates")
def list_testcase_report_templates():
    config = current_app.config["APP_CONFIG"]
    return ok({"list": list(available_templates(config.base_dir))})
