"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/auth/register", { method: "POST", body: form });
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="card form-card" style={{ padding: 26, margin: "30px auto", textAlign: "center" }}>
        <div style={{ fontSize: 44 }}>📬</div>
        <h1 style={{ margin: "8px 0 6px", fontSize: 22 }}>Check your inbox</h1>
        <p className="muted" style={{ margin: "0 0 14px" }}>
          We sent a verification link to <strong>{form.email}</strong>.
          Click it to activate your account — the link expires in 24&nbsp;hours.
        </p>
        <p className="muted" style={{ margin: "0 0 18px", fontSize: 13 }}>
          Local dev: the mail lands in the <a href="http://localhost:8025" target="_blank" rel="noreferrer">MailHog inbox</a>.
        </p>
        <Link className="btn btn-primary" style={{ display: "inline-block" }} href="/login">
          Go to login
        </Link>
      </div>
    );
  }

  return (
    <div className="card form-card" style={{ padding: 26, margin: "30px auto" }}>
      <h1 style={{ margin: "0 0 4px", fontSize: 22 }}>Create account</h1>
      <p className="muted" style={{ margin: "0 0 14px" }}>
        Takes ten seconds. We&apos;ll email you a verify link.
      </p>

      {error && <div className="msg-error">{error}</div>}

      <form onSubmit={submit}>
        <label className="label" htmlFor="full_name">Full name</label>
        <input
          id="full_name"
          className="input"
          required
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
        />

        <label className="label" htmlFor="email">Email</label>
        <input
          id="email"
          className="input"
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />

        <label className="label" htmlFor="password">Password (min 6 chars)</label>
        <input
          id="password"
          className="input"
          type="password"
          required
          minLength={6}
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />

        <button className="btn btn-primary" style={{ width: "100%", marginTop: 18 }} disabled={busy}>
          {busy ? "Creating…" : "Create account"}
        </button>
      </form>

      <p className="muted" style={{ marginTop: 14 }}>
        Already registered? <Link href="/login">Login</Link>
      </p>
    </div>
  );
}
