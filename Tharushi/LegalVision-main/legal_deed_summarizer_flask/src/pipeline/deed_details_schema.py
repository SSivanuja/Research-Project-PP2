COMMON_DEED_DETAILS_SCHEMA = {
  "document_title": "string|null",
  "deed_type": "string|null",
  "deed_number": "string|null",
  "prior_registration": "string|null",
  "execution_date": "string|null",
  "execution_place": "string|null",
  "notary_name": "string|null",
  "notary_address": "string|null",

  "parties": [
    {
      "role": "string|null",
      "name": "string|null",
      "nic": "string|null",
      "address": "string|null"
    }
  ],

  "consideration": {
    "amount_text": "string|null",
    "amount_numeric": "string|null",
    "payment_terms": "string|null"
  },

  "property": {
    "description": "string|null",
    "district": "string|null",
    "province": "string|null",
    "local_authority": "string|null",
    "gn_division": "string|null",
    "ds_division": "string|null",
    "extent": "string|null"
  },

  "key_obligations": ["string"],
  "key_rights": ["string"],
  "special_conditions": ["string"],

  "witnesses": [
    {"name": "string|null", "address": "string|null"}
  ],

  "important_dates": [
    {"label": "string|null", "date_text": "string|null", "source_quote": "string|null"}
  ],

  "traceability": [
    {"field": "string", "source_quote": "string|null"}
  ]
}