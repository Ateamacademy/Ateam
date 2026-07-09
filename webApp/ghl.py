"""GoHighLevel (GHL) CRM sync — pushes exam-interest registrations into GHL.

Env-gated like the Stripe integration: set
  GHL_PRIVATE_TOKEN  — a Private Integration token (GHL sub-account ->
                       Settings -> Private Integrations; needs Contacts write)
  GHL_LOCATION_ID    — the GHL sub-account (location) id
When either is unset (or the `requests` package is missing) every call is a
silent no-op, and a GHL failure must never block a registration, so everything
here is best-effort.

Design notes:
  * The upsert payload deliberately carries NO phone, so GHL dedupes on the
    student email only — siblings sharing a household number must not overwrite
    each other's contacts, and an unparseable phone must not cost us the lead.
    The phone is set afterwards by contact id, where it can fail harmlessly.
  * Kept free of app imports so it can be unit-tested standalone (test_ghl.py)
    and so tests can stub `ghl.requests`.
"""
import os
import re

try:
    import requests
except ImportError:  # optional dependency: the integration just stays dormant
    requests = None

API_BASE = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"   # GHL v2 API version header
TIMEOUT = 10                 # seconds; a slow CRM must not stall registrations


def enabled():
    return bool(requests is not None
                and os.environ.get("GHL_PRIVATE_TOKEN")
                and os.environ.get("GHL_LOCATION_ID"))


def _headers():
    return {
        "Authorization": f"Bearer {os.environ.get('GHL_PRIVATE_TOKEN')}",
        "Version": API_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _clean_phone(raw):
    """Digits (plus a leading +) only; None when there's no usable number."""
    if not raw:
        return None
    text = re.sub(r"[^0-9+]", "", str(raw))
    if "+" in text[1:]:
        text = text[0] + text[1:].replace("+", "")
    return text if len(re.sub(r"\D", "", text)) >= 7 else None


def sync_exam_interest(first_name, second_name, email, phone=None, tags=None, note=None):
    """Upsert the registrant as a GHL contact, then best-effort phone + note.

    Upsert (not create) so a repeat registration updates the same contact
    instead of duplicating it. Returns the GHL contact id, or None when the
    integration is disabled or the contact itself could not be created.
    """
    if not enabled():
        return None
    try:
        payload = {
            "locationId": os.environ.get("GHL_LOCATION_ID"),
            "firstName": (first_name or "").strip(),
            "lastName": (second_name or "").strip(),
            "email": (email or "").strip(),
            "tags": [t.strip() for t in (tags or []) if t and t.strip()],
            "source": "exam registration form",
        }
        resp = requests.post(f"{API_BASE}/contacts/upsert", json=payload,
                             headers=_headers(), timeout=TIMEOUT)
        resp.raise_for_status()
        contact_id = ((resp.json() or {}).get("contact") or {}).get("id")
        if not contact_id:
            print("GHL sync: upsert returned no contact id (non-fatal)")
            return None

        clean_phone = _clean_phone(phone)
        if clean_phone:
            try:
                phone_resp = requests.put(f"{API_BASE}/contacts/{contact_id}",
                                          json={"phone": clean_phone},
                                          headers=_headers(), timeout=TIMEOUT)
                phone_resp.raise_for_status()
            except Exception as phone_err:  # contact exists; phone is a bonus
                print(f"GHL phone update failed (non-fatal): {phone_err}")

        if note:
            try:
                note_resp = requests.post(f"{API_BASE}/contacts/{contact_id}/notes",
                                          json={"body": str(note)[:5000]},
                                          headers=_headers(), timeout=TIMEOUT)
                note_resp.raise_for_status()
            except Exception as note_err:  # contact exists; note is a bonus
                print(f"GHL note failed (non-fatal): {note_err}")

        return contact_id
    except Exception as exc:
        print(f"GHL sync failed (non-fatal): {exc}")
        return None
