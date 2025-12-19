def ok(data=None, msg=""):
    return {"code": 1000, "msg": msg or "成功", "data": data}

def err(code, msg, data=None):
    return {"code": int(code), "msg": msg, "data": data}