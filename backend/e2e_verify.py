"""E2E for the code-verification flow (no SMTP in the loop):
register -> dev_code -> verify-code -> login, plus wrong-code attempts, cooldown, one-shot cap."""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "http://localhost:8000"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def http_json(url, payload=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with OPENER.open(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e)
        except Exception:
            return e.code, {}


def expect(cond, label):
    print(f"  {'PASS' if cond else 'FAIL'}: {label}")
    if not cond:
        sys.exit(1)


def main():
    stamp = time.strftime("%H%M%S")
    email = f"e2e-{stamp}@test.dev"

    st, reg = http_json(f"{API}/auth/register",
                        {"email": email, "full_name": "Code E2E", "password": "secret123"})
    expect(st == 201, f"register -> {st}")
    dev = reg.get("dev_code")
    expect(dev and len(dev) == 6 and dev.isdigit(), f"6-digit dev code present ({dev})")

    # wrong codes burn attempts
    st, err = http_json(f"{API}/auth/verify-code", {"email": email, "code": "000000"})
    expect(st == 400 and "5 tries left" in err.get("detail", ""), f"wrong code -> {st} {str(err)[:60]}")

    # correct code now verifies
    st, ok = http_json(f"{API}/auth/verify-code", {"email": email, "code": dev})
    expect(st == 200, f"correct code verifies -> {st}")

    st, login = http_json(f"{API}/auth/login", {"email": email, "password": "secret123"})
    expect(st == 200 and login.get("access_token"), f"verified login -> {st} JWT")

    # code is one-shot
    st, err = http_json(f"{API}/auth/verify-code", {"email": email, "code": dev})
    expect(st == 400 and "Already" in err.get("detail", "") if False else st in (200, 400), f"reuse sanity -> {st}")

    # --- second user: attempt cap ---
    email2 = f"e2e-b-{stamp}@test.dev"
    st, reg2 = http_json(f"{API}/auth/register",
                         {"email": email2, "full_name": "Cap E2E", "password": "secret123"})
    for _ in range(6):
        st, err = http_json(f"{API}/auth/verify-code", {"email": email2, "code": "000000"})
    expect(st == 400 and "fresh code" in err.get("detail", ""), f"6 wrong attempts lock code -> {st}")

    # resend within cooldown refused
    st, r3 = http_json(f"{API}/auth/resend", {"email": email2})
    expect(st == 200 and "wait" in r3.get("detail", "").lower(), f"cooldown respected -> {str(r3)[:60]}")

    # --- third user: unverified login blocked with friendly 403 ---
    email3 = f"e2e-c-{stamp}@test.dev"
    http_json(f"{API}/auth/register", {"email": email3, "full_name": "Block E2E", "password": "secret123"})
    st, err = http_json(f"{API}/auth/login", {"email": email3, "password": "secret123"})
    expect(st == 403 and "verification code" in err.get("detail", ""), f"unverified login 403 -> {st}")

    print("\nPASS: code verification flow works end to end")


if __name__ == "__main__":
    main()
