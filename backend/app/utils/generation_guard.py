from functools import wraps

from flask import current_app


def reject_while_testcases_are_generating(view):
    @wraps(view)
    def wrapped(project_id, *args, **kwargs):
        current_app.extensions["testcase_job_manager"].ensure_not_generating(project_id)
        return view(project_id, *args, **kwargs)

    return wrapped
