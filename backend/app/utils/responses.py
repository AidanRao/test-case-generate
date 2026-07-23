from flask import jsonify


def ok(data):
    return jsonify({"code": 0, "message": "ok", "data": data})


def error(code, message, http_status=400, data=None):
    response = jsonify({"code": code, "message": message, "data": data or {}})
    response.status_code = http_status
    return response
