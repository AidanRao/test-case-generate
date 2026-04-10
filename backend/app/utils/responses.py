from flask import jsonify


def ok(data):
    return jsonify({"code": 0, "message": "ok", "data": data})


def error(code, message, http_status=400):
    response = jsonify({"code": code, "message": message, "data": {}})
    response.status_code = http_status
    return response
