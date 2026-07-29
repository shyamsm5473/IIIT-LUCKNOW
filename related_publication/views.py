"""
related_publication/views.py
──────────────────────────────────────────────────────────────────────────────
Functional API views for the Publication model.

Architecture decisions:
  - Pure Django (no DRF) — uses JsonResponse + request.method dispatch.
  - CSRF is enforced on every mutating method via Django's standard
    CsrfViewMiddleware (already active in settings MIDDLEWARE list).
    The JS layer reads the token from the 'csrftoken' cookie and sends
    it as the X-CSRFToken request header — the standard Django pattern.
  - All view functions are registered with @csrf_protect so mutations
    are explicitly guarded even if middleware ordering ever changes.
  - The page-render view (publications_page) uses @ensure_csrf_cookie
    so the browser always receives the csrftoken cookie on first load.
"""

import json

from django.http            import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import Publication


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: parse JSON body safely
# ──────────────────────────────────────────────────────────────────────────────

def _parse_json_body(request):
    """
    Decode the request body as JSON and return (data_dict, error_response).
    Returns (None, JsonResponse) on failure so callers can early-return.
    """
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object.")
        return data, None
    except (json.JSONDecodeError, ValueError) as exc:
        return None, JsonResponse({"success": False, "error": str(exc)}, status=400)


# ──────────────────────────────────────────────────────────────────────────────
# VIEW 1 — Page Render
# ──────────────────────────────────────────────────────────────────────────────

@ensure_csrf_cookie
def publications_page(request):
    """
    Render the related_publications.html template.

    @ensure_csrf_cookie guarantees the browser receives the 'csrftoken'
    cookie on this GET response, so subsequent fetch() POST/PUT/DELETE
    calls can read and forward it in X-CSRFToken headers.
    """
    from django.shortcuts import render
    return render(request, "related_publication/related_publications.html")


# ──────────────────────────────────────────────────────────────────────────────
# VIEW 2 — GET all publications  (/related_publication/api/publications/)
# ──────────────────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def api_get_publications(request):
    try:
        publications = Publication.objects.all()
        payload = [pub.to_dict() for pub in publications]
        return JsonResponse({"success": True, "data": payload}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


# ──────────────────────────────────────────────────────────────────────────────
# VIEW 3 — POST create new publication  (/related_publication/api/publications/add/)
# ──────────────────────────────────────────────────────────────────────────────

@csrf_protect
@require_http_methods(["POST"])
def api_add_publication(request):
    try:
        data, err = _parse_json_body(request)
        if err:
            return err

        # ── Mandatory field validation ─────────────────────────────────────
        required_fields = ("authors", "title", "journal", "year")
        missing = [f for f in required_fields if not str(data.get(f, "")).strip()]
        if missing:
            return JsonResponse(
                {"success": False, "error": f"Missing required fields: {', '.join(missing)}"},
                status=400
            )

        # ── Create & persist ───────────────────────────────────────────────
        pub = Publication.objects.create(
            authors   = data["authors"].strip(),
            title     = data["title"].strip(),
            journal   = data["journal"].strip(),
            year      = data["year"].strip(),
            link      = data.get("link", "").strip(),
            publisher = data.get("publisher", "").strip(),
            impact    = data.get("impact", "").strip(),
        )

        return JsonResponse({"success": True, "data": pub.to_dict()}, status=201)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


# ──────────────────────────────────────────────────────────────────────────────
# VIEW 4 — POST/PUT update existing  (/related_publication/api/publications/update/)
# ──────────────────────────────────────────────────────────────────────────────

@csrf_protect
@require_http_methods(["POST", "PUT"])
def api_update_publication(request):
    try:
        data, err = _parse_json_body(request)
        if err:
            return err

        record_id = data.get("id")
        if not record_id:
            return JsonResponse(
                {"success": False, "error": "Field 'id' is required for update operations."},
                status=400
            )

        # ── Fetch target record ────────────────────────────────────────────
        try:
            pub = Publication.objects.get(pk=record_id)
        except Publication.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": f"Publication with id={record_id} does not exist."},
                status=404
            )

        # ── Updateable field whitelist ─────────────────────────────────────
        updatable_fields = ("authors", "title", "journal", "year", "link", "publisher", "impact")
        for field in updatable_fields:
            if field in data:
                setattr(pub, field, str(data[field]).strip())

        pub.save()

        return JsonResponse({"success": True, "data": pub.to_dict()}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


# ──────────────────────────────────────────────────────────────────────────────
# VIEW 5 — DELETE remove record  (/related_publication/api/publications/delete/)
# ──────────────────────────────────────────────────────────────────────────────

@csrf_protect
@require_http_methods(["POST", "DELETE"])
def api_delete_publication(request):
    try:
        data, err = _parse_json_body(request)
        if err:
            return err

        record_id = data.get("id")
        if not record_id:
            return JsonResponse(
                {"success": False, "error": "Field 'id' is required for delete operations."},
                status=400
            )

        try:
            pub = Publication.objects.get(pk=record_id)
            pub.delete()
            return JsonResponse({"success": True, "deleted_id": record_id}, status=200)
        except Publication.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": f"Publication with id={record_id} does not exist."},
                status=404
            )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
