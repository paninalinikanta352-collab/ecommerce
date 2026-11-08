"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, formatINR, getToken } from "@/lib/api";

export default function OrderDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.push(`/login?next=/orders/${id}`);
      return;
    }
    api(`/orders/${id}`)
      .then(setOrder)
      .catch((e) => setError(e.message));
  }, [id, router]);

  if (error) return <div className="msg-error">{error}</div>;
  if (!order) return <p className="muted">Loading…</p>;

  return (
    <div style={{ maxWidth: 640 }}>
      <p>
        <Link className="muted" href="/orders">
          ← All my orders
        </Link>
      </p>

      <h1>Order #{order.id}</h1>
      <p>
        <span className={`badge badge-${order.status}`}>{order.status}</span>{" "}
        <span className="muted">{new Date(order.created_at).toLocaleString()}</span>
      </p>

      {order.status !== "paid" && order.status !== "delivered" && (
        <div className="msg-error">
          Payment {order.status === "created" ? "not completed yet" : `is ${order.status}`}.
          {order.status === "created" && " If it was deducted, it will auto-refund."}
        </div>
      )}

      <div className="card" style={{ padding: 18, marginTop: 14 }}>
        {order.items.map((item) => (
          <div
            key={item.id}
            style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}
          >
            <span>
              {item.product_name}{" "}
              <span className="muted">× {item.quantity}</span>
            </span>
            <strong>{formatINR(item.unit_price_paise * item.quantity)}</strong>
          </div>
        ))}
        <div className="total-row">
          <span>Total paid</span>
          <span>{formatINR(order.total_paise)}</span>
        </div>
        {order.razorpay_payment_id && (
          <p className="muted" style={{ fontSize: 12 }}>
            Payment ID: {order.razorpay_payment_id}
          </p>
        )}
      </div>

      <div className="card" style={{ padding: 18, marginTop: 14 }}>
        <h2 style={{ margin: "0 0 8px", fontSize: 16 }}>Shipping to</h2>
        <p style={{ margin: 0 }}>
          {order.shipping_name}
          <br />
          {order.shipping_address}
          <br />
          Phone: {order.shipping_phone}
        </p>
      </div>
    </div>
  );
}
