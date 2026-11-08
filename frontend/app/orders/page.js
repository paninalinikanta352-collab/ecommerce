"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, formatINR, getToken } from "@/lib/api";

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login?next=/orders");
      return;
    }
    api("/orders")
      .then(setOrders)
      .catch((e) => setError(e.message));
  }, [router]);

  if (error) return <div className="msg-error">{error}</div>;
  if (!orders) return <p className="muted">Loading…</p>;

  return (
    <div>
      <h1>My orders</h1>

      {orders.length === 0 && (
        <p className="muted">No orders yet. <Link href="/products">Start shopping →</Link></p>
      )}

      {orders.map((order) => (
        <Link href={`/orders/${order.id}`} key={order.id} className="card" style={{ display: "block", padding: 16, margin: "14px 0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <strong>Order #{order.id}</strong>
              <div className="muted">{new Date(order.created_at).toLocaleString()}</div>
            </div>
            <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
              <strong>{formatINR(order.total_paise)}</strong>
              <span className={`badge badge-${order.status}`}>{order.status}</span>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
