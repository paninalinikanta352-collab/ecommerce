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

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api("/auth/register", { method: "POST", body: form });
      // dev mode: the code comes back so the verify page can show it on screen;
      // production: nothing rides the response — the code gets emailed instead
      if (r.dev_code) {
        sessionStorage.setItem("verifyDevCode", r.dev_code);
        sessionStorage.setItem("verifyDevEmail", r.email);
      }
      router.push(`/verify?email=${encodeURIComponent(r.email)}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card form-card" style={{ padding: 26, margin: "30px auto" }}>
      <h1 style={{ margin: "0 0 4px", fontSize: 22 }}>Create account</h1>
      <p className="muted" style={{ margin: "0 0 14px" }}>
        Takes ten seconds. You&apos;ll get a 6-digit code.
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
