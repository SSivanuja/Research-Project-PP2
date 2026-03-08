def build_common_infographic(details: dict) -> dict:
    parties = details.get("parties") or []
    consideration = details.get("consideration") or {}
    prop = details.get("property") or {}

    obligations = (details.get("key_obligations") or [])[:4]
    conditions = (details.get("special_conditions") or [])[:4]

    return {
        "template_id": "COMMON_DEED_V1",
        "header": {
            "title": details.get("document_title") or "LEGAL DEED",
            "deed_type": details.get("deed_type"),
            "deed_number": details.get("deed_number"),
            "execution_date": details.get("execution_date"),
            "execution_place": details.get("execution_place"),
        },
        "parties": parties[:6],
        "money": {
            "amount_text": consideration.get("amount_text"),
            "amount_numeric": consideration.get("amount_numeric"),
            "payment_terms": consideration.get("payment_terms"),
        },
        "property": {
            "description": prop.get("description"),
            "district": prop.get("district"),
            "local_authority": prop.get("local_authority"),
            "extent": prop.get("extent"),
        },
        "notary": {
            "name": details.get("notary_name"),
            "address": details.get("notary_address"),
        },
        "highlights": {
            "key_obligations": obligations,
            "special_conditions": conditions,
        },
        "traceability": (details.get("traceability") or [])[:10],
    }