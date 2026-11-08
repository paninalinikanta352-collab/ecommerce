"""Full E2E for the verification flow, MailHog-safe extraction:
register -> read mail -> decode QP/soft-wraps -> verify -> login -> one-use check -> resend.

Run:  .venv\\Scripts\\python.exe e2e_verify.py            # full flow, consumes the token
      .venv\\Scripts\\python.exe e2e_verify.py --preserve # register + print link, leave token unused
"""
import sys
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

API = "http://localhost:8000"
MH = "http://localhost:8025/api/v2/messages"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def http_json(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with OPENER.open(req) as r:
            return r.status, r.headers.get("Location"), json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.headers.get("Location"), json.load(e)
        except Exception:
            return e.code, e.headers.get("Location"), {}


def decoded_body(item):
    """Concatenate every part, undoing quoted-printable ('=3D', soft wraps)."""
    chunks = []
    for part in item["MIME"]["Parts"]:
        body = part.get("Body", "")
        body = re.sub(r"=\r?\n", "", body)          # QP soft line breaks
        body = body.replace("=3D", "=").replace("=3d", "=")
        chunks.append(body)
    return "\n".join(chunks)


def extract_token(text):
    m = re.search(r"token=([A-Za-z0-9_-]+)", text)
    return m.group(1) if m else None


def main():
    stamp = time.strftime("%H%M%S")
    email = f"e2e-{stamp}@test.dev"
    preserve = "--preserve" in sys.argv
    st, _, reg = http_json(f"{API}/auth/register",
                           {"email": email, "full_name": "E2E", "password": "secret123"})
    print(f"register -> {st} {reg.get('detail')}")
    assert st == 201, "register failed"

    time.sleep(0.8)
    st, _, mh = http_json(MH)
    item = next((i for i in mh["items"]
                 if i["To"][0]["Mailbox"] + "@" + i["To"][0]["Domain"] == email), None)
    assert item, "mail not found"
    body = decoded_body(item)
    tok = extract_token(body)
    print(f"mail received: subject={item['Content']['Headers']['Subject'][0]!r} token_len={len(tok)}")
    assert tok and len(tok) == 32, f"unexpected token len {len(tok)}"

    if preserve:
        print(f"LINK={API.replace('8000', '3000')}/verify?token={tok}")
        print(f"EMAIL={email}")
        print(f"PASSWORD=secret123")
        return

    st, loc, _ = http_json(f"{API}/auth/verify?token={urllib.parse.quote(tok)}")
    print(f"fresh link  -> {st} {loc}")
    assert (loc or "").endswith("status=ok"), "verify did not return ok"

    st, _, login = http_json(f"{API}/auth/login", {"email": email, "password": "secret123"})
    jwt = (login or {}).get("access_token", "")
    print(f"login       -> {st} ({'JWT ' + str(len(jwt)) + ' chars' if jwt else 'FAIL'})")
    assert st == 200 and jwt, "verified login failed"

    st, loc, _ = http_json(f"{API}/auth/verify?token={urllib.parse.quote(tok)}")
    print(f"link reuse  -> {st} {loc} (expect invalid)")
    assert (loc or "").endswith("status=invalid"), "one-use enforcement failed"

    print("\nPASS: full verification flow works end to end")


if __name__ == "__main__":
    main()
