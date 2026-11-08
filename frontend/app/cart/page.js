"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, formatINR, getToken } from "@/lib/api";

export default function CartPage() {
  const router = useRouter();
  const [cart, setCart] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login?next=/cart");
      return;
    }
    api("/cart")
      .then(setCart)
      .catch((e) => setError(e.message));
  }, [router]);

  async function changeQty(item, quantity) {
    try {
      const updated = await api(`/cart/items/${item.id}`, {
        method: "PATCH",
        body: { quantity },
      });
      setCart(updated);
      window.dispatchEvent(new Event("cart-updated"));
    } catch (e) {
      setError(e.message);
    }
  }

  async function removeItem(item) {
    try {
      await api(`/cart/items/${item.id}`, { method: "DELETE" });
      const updated = await api("/cart");
      setCart(updated);
      window.dispatchEvent(new Event("cart-updated"));
    } catch (e) {
      setError(e.message);
    }
  }

  if (error) return <div className="msg-error">{error}</div>;
  if (!cart) return <p className="muted">Loading…</p>;

  if (cart.items.length === 0) {
    return (
      <div>
        <h1>Your cart</h1>
        <p className="muted">Nothing in here yet.</p>
        <Link className="btn btn-primary" href="/products">
          Browse products
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1>Your cart</h1>

      <div style={{ marginTop: 18 }}>
        {cart.items.map((item) => (
          <div
            key={item.id}
            className="card"
            style={{
              display: "flex",
              gap: 16,
              alignItems: "center",
              padding: 12,
              marginBottom: 12,
            }}
          >
            <img
              src={item.product.image_url}
              alt={item.product.name}
              style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 8 }}
            />
            <div style={{ flex: 1 }}>
              <Link href={`/products/${item.product.slug}`} style={{ fontWeight: 600 }}>
                {item.product.name}
              </Link>
              <div className="muted">{formatINR(item.product.price_paise)} each</div>
            </div>
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <button
                className="btn btn-outline"
                style={{ padding: "4px 10px" }}
                disabled={item.quantity <= 1}
                onClick={() => changeQty(item, item.quantity - 1)}
              >
                −
              </button>
              <span style={{ width: 26, textAlign: "center" }}>{item.quantity}</span>
              <button
                className="btn btn-outline"
                style={{ padding: "4px 10px" }}
                disabled={item.quantity >= item.product.stock}
                onClick={() => changeQty(item, item.quantity + 1)}
              >
                +
              </button>
            </div>
            <div style={{ width: 90, textAlign: "right", fontWeight: 700 }}>
              {formatINR(item.product.price_paise * item.quantity)}
            </div>
            <button className="btn btn-danger" onClick={() => removeItem(item)}>
              Remove
            </button>
          </div>
        ))}
      </div>

      <div className="card" style={{ padding: 18, maxWidth: 380, marginTop: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span className="muted">Items total</span>
          <span>{formatINR(cart.total_paise)}</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span className="muted">Shipping</span>
          <span>Free</span>
        </div>
        <div className="total-row">
          <span>Total</span>
          <span>{formatINR(cart.total_paise)}</span>
        </div>
        <Link className="btn btn-primary" href="/checkout" style={{ width: "100%" }}>
          Proceed to checkout
        </Link>
      </div>
    </div>
  );
}
