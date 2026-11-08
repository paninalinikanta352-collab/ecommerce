"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { api } from "@/lib/api";

function VerifyInner() {
  const params = useSearchParams();
  const [email, setEmail] = useState(params.get("email") ?? "");
  const [code, setCode] = useState("");
  const [devCode, setDevCode] = useState(() => {
    try {
      const c = sessionStorage.getItem("verifyDevCode");
      if (c) {
        sessionStorage.removeItem("verifyDevCode");
        sessionStorage.removeItem("verifyDevEmail");
      }
      return c;
    } catch {
      return null;
    }
  });
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api("/auth/verify-code", {
        method: "POST",
        body: { email, code },
      });
      setDone(true);
      setNotice(r.detail === "verified" ? "" : r.detail);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    if (!email) {
      setError("Type your email first.");
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const r = await api("/auth/resend", { method: "POST", body: { email } });
      setNotice(r.detail);
      if (r.dev_code) setDevCode(r.dev_code);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="card form-card" style={{ padding: 26, margin: "30px auto", textAlign: "center" }}>
        <div style={{ fontSize: 44 }}>✅</div>
        <h1 style={{ margin: "8px 0 6px", fontSize: 22 }}>Account verified</h1>
        <p className="muted" style={{ margin: "0 0 18px" }}>You can log in now.</p>
        <Link className="btn btn-primary" style={{ display: "inline-block" }} href="/login">
          Login
        </Link>
      </div>
    );
  }

  return (
    <div className="card form-card" style={{ padding: 26, margin: "30px auto" }}>
      <h1 style={{ margin: "0 0 4px", fontSize: 22 }}>Verify your email</h1>
      <p className="muted" style={{ margin: "0 0 14px" }}>
        Enter the 6-digit code to activate your account. It expires in 10 minutes.
      </p>

      {devCode && (
        <div className="msg-ok" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 15 }}>No email service here — your code:</div>
          <div
            style={{
              fontSize: 32,
              fontWeight: 700,
              letterSpacing: 10,
              fontFamily: "monospace",
              padding: "6px 0",
            }}
          >
            {devCode}
          </div>
          <div style={{ fontSize: 12 }}>
            With a real SMTP configured in <code>.env</code>, this code would instead arrive by email.
          </div>
        </div>
      )}

      {error && <div className="msg-error">{error}</div>}
      {notice && <div className="msg-ok">{notice}</div>}

      <form onSubmit={submit}>
        <label className="label" htmlFor="verify-email">Email</label>
        <input
          id="verify-email"
          className="input"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <label className="label" htmlFor="verify-code">6-digit code</label>
        <input
          id="verify-code"
          className="input"
          inputMode="numeric"
          pattern="\d{6}"
          maxLength={6}
          autoComplete="one-time-code"
          required
          style={{ letterSpacing: 8, fontSize: 18, textAlign: "center", fontFamily: "monospace" }}
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
        />

        <button className="btn btn-primary" style={{ width: "100%", marginTop: 18 }} disabled={busy}>
          {busy ? "Checking…" : "Verify"}
        </button>
      </form>

      <button className="btn" style={{ width: "100%", marginTop: 10 }} onClick={resend} disabled={busy}>
        Send a new code
      </button>

      <p className="muted" style={{ marginTop: 14 }}>
        No account? <Link href="/register">Register</Link>
      </p>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={null}>
      <VerifyInner />
    </Suspense>
  );
}
