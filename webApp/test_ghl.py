"""Standalone tests for the GoHighLevel sync module (no Flask/DB, no network).

Run:  python3 test_ghl.py   (needs the `requests` package importable)
"""
import os

import ghl


def check(name, cond):
    print(("PASS" if cond else "FAIL") + " - " + name)
    if not cond:
        raise AssertionError(name)


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    def json(self):
        return self._payload


class FakeRequests:
    """Captures every call; configurable failures per endpoint."""
    def __init__(self, fail_upsert=False, fail_phone=False, fail_note=False):
        self.calls = []
        self.fail_upsert = fail_upsert
        self.fail_phone = fail_phone
        self.fail_note = fail_note

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"method": "POST", "url": url, "json": json,
                           "headers": headers, "timeout": timeout})
        if url.endswith("/contacts/upsert"):
            if self.fail_upsert:
                raise RuntimeError("boom")
            return FakeResponse({"contact": {"id": "ghl-c-1"}})
        if url.endswith("/notes"):
            return FakeResponse({}, status=403 if self.fail_note else 200)
        return FakeResponse({})

    def put(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"method": "PUT", "url": url, "json": json,
                           "headers": headers, "timeout": timeout})
        return FakeResponse({}, status=422 if self.fail_phone else 200)


def _set_env():
    os.environ["GHL_PRIVATE_TOKEN"] = "pit-test-token"
    os.environ["GHL_LOCATION_ID"] = "loc-test-1"


def _clear_env():
    os.environ.pop("GHL_PRIVATE_TOKEN", None)
    os.environ.pop("GHL_LOCATION_ID", None)


def test_disabled_is_noop():
    _clear_env()
    fake = FakeRequests()
    ghl.requests = fake
    result = ghl.sync_exam_interest("A", "B", "a@b.test", tags=["x"], note="n")
    check("disabled -> returns None", result is None)
    check("disabled -> zero network calls", fake.calls == [])


def test_upsert_then_phone_then_note():
    _set_env()
    fake = FakeRequests()
    ghl.requests = fake
    result = ghl.sync_exam_interest(
        " Jane ", "Doe", "jane@example.test", phone=" 07123 456789 ",
        tags=["exam interest", "gcse", "", None, " cov rd "],
        note="Quoted: £48.00\nRequested exams:\n- GCSE Maths")
    check("returns the GHL contact id", result == "ghl-c-1")
    check("three calls: upsert + phone + note", len(fake.calls) == 3)

    upsert = fake.calls[0]
    check("hits the v2 upsert endpoint", upsert["url"].endswith("/contacts/upsert"))
    check("bearer token header",
          upsert["headers"]["Authorization"] == "Bearer pit-test-token")
    check("version header present", upsert["headers"]["Version"] == ghl.API_VERSION)
    body = upsert["json"]
    check("location id in payload", body["locationId"] == "loc-test-1")
    check("names trimmed", body["firstName"] == "Jane" and body["lastName"] == "Doe")
    check("NO phone in the upsert (email-only dedupe)", "phone" not in body)
    check("blank tags dropped, kept ones trimmed",
          body["tags"] == ["exam interest", "gcse", "cov rd"])
    check("timeout set", upsert["timeout"] == ghl.TIMEOUT)

    phone_call = fake.calls[1]
    check("phone set by contact id (PUT)",
          phone_call["method"] == "PUT" and phone_call["url"].endswith("/contacts/ghl-c-1"))
    check("phone sanitised to digits", phone_call["json"]["phone"] == "07123456789")

    note = fake.calls[2]
    check("note posted to the contact", note["url"].endswith("/contacts/ghl-c-1/notes"))
    check("note body carried", "GCSE Maths" in note["json"]["body"])


def test_bad_phone_never_costs_the_lead():
    _set_env()
    # unusable phone -> skipped entirely, contact still created
    fake = FakeRequests()
    ghl.requests = fake
    result = ghl.sync_exam_interest("A", "B", "a@b.test", phone="n/a")
    check("junk phone skipped, contact created", result == "ghl-c-1")
    check("no phone call for junk phone",
          all(c["method"] == "POST" for c in fake.calls))
    # GHL rejecting the phone (422) is non-fatal too
    fake = FakeRequests(fail_phone=True)
    ghl.requests = fake
    result = ghl.sync_exam_interest("A", "B", "a@b.test", phone="07123456789",
                                    note="n")
    check("phone 422 -> contact id still returned", result == "ghl-c-1")
    check("note still posted after phone failure",
          any(c["url"].endswith("/notes") for c in fake.calls))


def test_note_http_error_is_caught():
    _set_env()
    fake = FakeRequests(fail_note=True)
    ghl.requests = fake
    result = ghl.sync_exam_interest("A", "B", "a@b.test", note="n")
    check("note 403 -> contact id still returned", result == "ghl-c-1")


def test_upsert_failure_is_nonfatal():
    _set_env()
    ghl.requests = FakeRequests(fail_upsert=True)
    result = ghl.sync_exam_interest("A", "B", "a@b.test")
    check("network failure -> None, no raise", result is None)


def test_clean_phone():
    check("spaces stripped", ghl._clean_phone("07123 456 789") == "07123456789")
    check("+44 kept", ghl._clean_phone("+44 7123 456789") == "+447123456789")
    check("letters dropped entirely", ghl._clean_phone("mum: no phone") is None)
    check("too short -> None", ghl._clean_phone("07000 1") is None)
    check("None -> None", ghl._clean_phone(None) is None)


if __name__ == "__main__":
    for fn in [test_disabled_is_noop, test_upsert_then_phone_then_note,
               test_bad_phone_never_costs_the_lead, test_note_http_error_is_caught,
               test_upsert_failure_is_nonfatal, test_clean_phone]:
        print(f"\n# {fn.__name__}")
        fn()
    _clear_env()
    print("\nAll GHL tests passed.")
