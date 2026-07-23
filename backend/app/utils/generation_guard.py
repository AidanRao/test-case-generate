from functools import wraps

from flask import current_app

from app.utils.responses import error


def reject_while_testcases_are_generating(view):
    @wraps(view)
    def wrapped(project_id, *args, **kwargs):
        manager = current_app.extensions["testcase_job_manager"]
        if manager.has_active_project(project_id):
            return error(
                40902,
                "测试用例生成期间不能修改项目数据",
                409,
                manager.get_project_status(project_id),
            )
        return view(project_id, *args, **kwargs)

    return wrapped
