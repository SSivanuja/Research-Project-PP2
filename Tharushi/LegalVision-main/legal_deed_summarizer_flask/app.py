import os
import uuid
from flask import Flask, jsonify, request
from flask_cors import CORS

from dotenv import load_dotenv
load_dotenv()  # ✅ loads .env from same folder as app.py (backend root)



from src.pipeline.resources import get_resources, spacy_status
from src.pipeline.orchestrator import run_full_pipeline, extract_timeline_pipeline
from src.utils.validation import (
    require_json,
    require_field_str,
    require_bool_optional,
)

# ✅ Universal reader (txt/pdf/docx/images)
from src.utils.io import read_uploaded_file

# ✅ Gemini deed detail extractor
from src.pipeline.deed_details_extractor import extract_deed_details_with_gemini
from src.pipeline.infographic_common import build_common_infographic


def create_app() -> Flask:
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(
        app,
        resources={
            r"/api/*": {"origins": "*"},
            r"/health": {"origins": "*"},
            r"/": {"origins": "*"},
        },
    )

    # ---------- Load resources ONCE at startup (cached) ----------
    resources = get_resources()

    # ---------- Home route (prevents 404 on /) ----------
    @app.get("/")
    def home():
        return jsonify(
            {
                "message": "Legal Deed Summarizer API is running",
                "routes": {
                    "home": "GET /",
                    "health": "GET /health",
                    "summarize_text": "POST /api/summarize-text",
                    "summarize_file": "POST /api/summarize-file",
                    "extract_timeline": "POST /api/extract-timeline",
                    "extract_timeline_file": "POST /api/extract-timeline-file",
                    # ✅ NEW
                    "extract_deed_details_text": "POST /api/extract-deed-details-text",
                    "extract_deed_details_file": "POST /api/extract-deed-details-file",
                },
                "supported_upload_formats": [".txt", ".pdf", ".docx", ".png", ".jpg", ".jpeg"],
            }
        )

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "healthy",
                "model": {
                    "clause_classifier": resources["classifier"]["model_dir"],
                    "summarizer_loaded_from": resources["summarizer"]["loaded_from"],
                    "summarizer_model_name": resources["summarizer"]["model_name"],
                },
                "device": resources["device"],
                "glossary_loaded": bool(resources["glossary"]),
                "spacy": spacy_status(),
            }
        )

    # ==========================================================
    # Summarization APIs
    # ==========================================================
    @app.post("/api/summarize-text")
    def summarize_text():
        payload = require_json(request)

        document_id = payload.get("document_id") or str(uuid.uuid4())
        text = require_field_str(payload, "text")
        traceability = require_bool_optional(payload, "traceability", default=True)

        result = run_full_pipeline(
            document_id=document_id,
            raw_text=text,
            traceability=traceability,
            resources=resources,
        )
        return jsonify(result)

    @app.post("/api/summarize-file")
    def summarize_file():
        if "file" not in request.files:
            return jsonify({"error": "Missing file field 'file' in multipart/form-data"}), 400

        f = request.files["file"]
        if not f.filename:
            return jsonify({"error": "Uploaded file has no filename"}), 400

        document_id = request.form.get("document_id") or str(uuid.uuid4())
        traceability_str = request.form.get("traceability", "true").lower()
        traceability = traceability_str in ("true", "1", "yes", "y")

        try:
            text = read_uploaded_file(f)
        except Exception as e:
            return jsonify({"error": f"Failed to read uploaded file: {str(e)}"}), 400

        if not str(text).strip():
            return (
                jsonify(
                    {
                        "error": "No readable text was extracted from the uploaded file. "
                                 "If this is a scanned PDF/image, ensure OCR (Tesseract) is installed and configured."
                    }
                ),
                400,
            )

        result = run_full_pipeline(
            document_id=document_id,
            raw_text=text,
            traceability=traceability,
            resources=resources,
        )
        return jsonify(result)

    # ==========================================================
    # Timeline Extraction APIs
    # ==========================================================
    @app.post("/api/extract-timeline")
    def extract_timeline_text():
        payload = require_json(request)

        document_id = payload.get("document_id") or str(uuid.uuid4())
        text = require_field_str(payload, "text")
        include_relative_deadlines = require_bool_optional(
            payload, "include_relative_deadlines", default=True
        )

        result = extract_timeline_pipeline(
            document_id=document_id,
            text=text,
            include_relative_deadlines=include_relative_deadlines,
        )
        return jsonify(result)

    @app.post("/api/extract-timeline-file")
    def extract_timeline_file():
        if "file" not in request.files:
            return jsonify({"error": "Missing file field 'file' in multipart/form-data"}), 400

        document_id = request.form.get("document_id") or str(uuid.uuid4())
        include_relative_deadlines = (
            request.form.get("include_relative_deadlines", "true").strip().lower()
            in ("true", "1", "yes", "y")
        )

        try:
            text = read_uploaded_file(request.files["file"])
        except Exception as e:
            return jsonify({"error": f"Failed to read uploaded file: {str(e)}"}), 400

        if not str(text).strip():
            return (
                jsonify(
                    {
                        "error": "No readable text was extracted from the uploaded file. "
                                 "If this is a scanned PDF/image, ensure OCR (Tesseract) is installed and configured."
                    }
                ),
                400,
            )

        result = extract_timeline_pipeline(
            document_id=document_id,
            text=text,
            include_relative_deadlines=include_relative_deadlines,
        )
        return jsonify(result)

    # ==========================================================
    # ✅ NEW: Deed Details Extraction APIs (Gemini)
    # ==========================================================
    @app.post("/api/extract-deed-details-text")
    def extract_deed_details_text():
        payload = require_json(request)

        document_id = payload.get("document_id") or str(uuid.uuid4())
        text = require_field_str(payload, "text")

        try:
            details = extract_deed_details_with_gemini(text)
        except Exception as e:
            return jsonify({"error": f"Gemini extraction failed: {str(e)}"}), 500

        return jsonify({"document_id": document_id, "deed_details": details})

    @app.post("/api/extract-deed-details-file")
    def extract_deed_details_file():
        if "file" not in request.files:
            return jsonify({"error": "Missing file field 'file' in multipart/form-data"}), 400

        f = request.files["file"]
        if not f.filename:
            return jsonify({"error": "Uploaded file has no filename"}), 400

        document_id = request.form.get("document_id") or str(uuid.uuid4())

        try:
            text = read_uploaded_file(f)
        except Exception as e:
            return jsonify({"error": f"Failed to read uploaded file: {str(e)}"}), 400

        if not str(text).strip():
            return jsonify({"error": "No readable text extracted from file."}), 400

        try:
            details = extract_deed_details_with_gemini(text)
        except Exception as e:
            return jsonify({"error": f"Gemini extraction failed: {str(e)}"}), 500

        return jsonify({"document_id": document_id, "deed_details": details})
    

        # ==========================================================
    # ✅ NEW: Generate Common Infographic (from deed_details)
    # ==========================================================
    @app.post("/api/generate-common-infographic")
    def generate_common_infographic():
        payload = require_json(request)
        details = payload.get("deed_details")

        if not isinstance(details, dict):
            return jsonify({"error": "Missing deed_details object"}), 400

        infographic = build_common_infographic(details)
        return jsonify({"infographic": infographic})

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # If debug reload loads models twice, set use_reloader=False
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)