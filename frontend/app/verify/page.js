"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

const STATES = {
  ok: {
    emoji: "✅",
    title: "Email verified",
    body: "Your account is active. Log in and start shopping.",
    cta: "Login",
  },
  expired: {
    emoji: "⏰",
    title: "Link expired",
    body: "That verification link is older than 24 hours. Go to login and request a fresh one.",
    cta: "Login",
  },
  invalid: {
    emoji: "🚫",
    title: "Invalid link",
    body: "This link is broken or was already used. You can request a new one from the login page.",
    cta: "Login",
  },
};

function VerifyInner() {
  const params = useSearchParams();
  const s = STATES[params.get("status")] ?? {
    emoji: "📬",
    title: "Waiting for verification",
    body: "Follow the verification link in the email we sent you — this page shows the result when you do.",
    cta: "Login",
  };

  return (
    <div className="card form-card" style={{ padding: 26, margin: "30px auto", textAlign: "center" }}>
      <div style={{ fontSize: 44 }}>{s.emoji}</div>
      <h1 style={{ margin: "8px 0 6px", fontSize: 22 }}>{s.title}</h1>
      <p className="muted" style={{ margin: "0 0 18px" }}>{s.body}</p>
      <Link className="btn btn-primary" style={{ display: "inline-block" }} href="/login">
        {s.cta}
      </Link>
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
