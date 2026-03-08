from flask import Request

def require_json(request: Request) -> dict:
    if not request.is_json:
        raise ValueError("Request must be application/json")
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValueError("Invalid JSON body")
    return payload

def require_field_str(payload: dict, field: str) -> str:
    if field not in payload:
        raise ValueError(f"Missing required field '{field}'")
    val = payload[field]
    if not isinstance(val, str) or not val.strip():
        raise ValueError(f"Field '{field}' must be a non-empty string")
    return val

def require_bool_optional(payload: dict, field: str, default: bool = True) -> bool:
    if field not in payload:
        return default
    val = payload[field]
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ("true", "1", "yes", "y"):
            return True
        if v in ("false", "0", "no", "n"):
            return False
    raise ValueError(f"Field '{field}' must be boolean (true/false)")
