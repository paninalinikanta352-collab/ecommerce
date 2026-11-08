"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";
import { Suspense, useState } from "react";
import { api, saveAuth } from "@/lib/api";

function LoginInner() {
  const params = useSearchParams();
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [needsVerify, setNeedsVerify] = useState(false);
  const [resendMsg, setResendMsg] = useState("");
  const [resendBusy, setResendBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResendMsg("");
    try {
      const token = await api("/auth/login", { method: "POST", body: form });
      saveAuth(token.access_token);
      const me = await api("/auth/me");
      const next = params.get("next");
      if (next) router.push(next);
      else if (me.is_admin) router.push("/admin");
      else router.push("/");
    } catch (err) {
      setError(err.message);
      if (err.message.includes("Verify your email")) setNeedsVerify(true);
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    if (!form.email) {
      setResendMsg("Type your email first.");
      return;
    }
    setResendBusy(true);
    setResendMsg("");
    try {
      const r = await api("/auth/resend", {
        method: "POST",
        body: { email: form.email },
      });
      setResendMsg(r.detail);
    } catch (err) {
      setResendMsg(err.message);
    } finally {
      setResendBusy(false);
    }
  }

  return (
    <div className="card form-card" style={{ padding: 26, margin: "30px auto" }}>
      <h1 style={{ margin: "0 0 4px", fontSize: 22 }}>Login</h1>
      <p className="muted" style={{ margin: "0 0 14px" }}>
        Welcome back.
      </p>

      {error && <div className="msg-error">{error}</div>}
      {resendMsg && <div className="msg-ok">{resendMsg}</div>}

      <form onSubmit={submit}>
        <label className="label" htmlFor="email">Email</label>
        <input
          id="email"
          className="input"
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />

        <label className="label" htmlFor="password">Password</label>
        <input
          id="password"
          className="input"
          type="password"
          required
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />

        <button className="btn btn-primary" style={{ width: "100%", marginTop: 18 }} disabled={busy}>
          {busy ? "Logging in…" : "Login"}
        </button>
      </form>

      {needsVerify && (
        <button
          className="btn"
          style={{ width: "100%", marginTop: 10 }}
          onClick={resend}
          disabled={resendBusy}
        >
          {resendBusy ? "Sending…" : "Resend verification email"}
        </button>
      )}

      <p className="muted" style={{ marginTop: 14 }}>
        No account? <Link href="/register">Register</Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginInner />
    </Suspense>
  );
}
