"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, formatINR, getToken } from "@/lib/api";

function loadRazorpayScript() {
  if (typeof window === "undefined") return Promise.resolve(false);
  if (window.Razorpay) return Promise.resolve(true);
  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function CheckoutPage() {
  const router = useRouter();
  const [cart, setCart] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    shipping_name: "",
    shipping_phone: "",
    shipping_address: "",
  });

  useEffect(() => {
    if (!getToken()) {
      router.push("/login?next=/checkout");
      return;
    }
    api("/cart")
      .then((c) => {
        setCart(c);
        if (c.items.length === 0) router.push("/cart");
      })
      .catch((e) => setError(e.message));
  }, [router]);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function pay() {
    setBusy(true);
    setError("");
    try {
      const ready = await loadRazorpayScript();
      if (!ready) throw new Error("Could not load Razorpay. Check your connection.");

      // 1. backend creates the order row + a Razorpay order
      const checkout = await api("/orders", { method: "POST", body: form });

      // 2. open the Razorpay modal
      const rzp = new window.Razorpay({
        key: checkout.razorpay_key_id,
        amount: checkout.amount_paise,
        currency: "INR",
        name: checkout.name,
        order_id: checkout.razorpay_order_id,
        prefill: {
          name: form.shipping_name,
          email: checkout.email,
          contact: form.shipping_phone,
        },
        handler: async (response) => {
          // 3. backend verifies the signature, marks paid, clears the cart
          try {
            const order = await api("/orders/verify", { method: "POST", body: response });
            window.dispatchEvent(new Event("cart-updated"));
            router.push(`/orders/${order.id}`);
          } catch (e) {
            setError(e.message);
            setBusy(false);
          }
        },
        modal: {
          ondismiss: () => setBusy(false),
        },
      });
      rzp.open();
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  if (!cart) return <p className="muted">{error || "Loading…"}</p>;
  if (error && cart.items.length === 0) return <div className="msg-error">{error}</div>;

  return (
    <div className="detail-layout" style={{ gridTemplateColumns: "1fr 380px" }}>
      <div>
        <h1>Checkout</h1>
        <p className="muted">Delivery details</p>

        <label className="label" htmlFor="shipping_name">
          Full name
        </label>
        <input
          id="shipping_name"
          className="input"
          value={form.shipping_name}
          onChange={(e) => update("shipping_name", e.target.value)}
        />

        <label className="label" htmlFor="shipping_phone">
          Phone
        </label>
        <input
          id="shipping_phone"
          className="input"
          placeholder="9876543210"
          value={form.shipping_phone}
          onChange={(e) => update("shipping_phone", e.target.value)}
        />

        <label className="label" htmlFor="shipping_address">
          Address
        </label>
        <textarea
          id="shipping_address"
          className="input"
          rows={4}
          placeholder="House, street, city, state, PIN"
          value={form.shipping_address}
          onChange={(e) => update("shipping_address", e.target.value)}
        />
      </div>

      <div className="card" style={{ padding: 18, top: 20, position: "sticky" }}>
        <h2 style={{ margin: "0 0 12px", fontSize: 17 }}>Order summary</h2>
        {cart.items.map((item) => (
          <div
            key={item.id}
            style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}
          >
            <span className="muted">
              {item.product.name} × {item.quantity}
            </span>
            <span>{formatINR(item.product.price_paise * item.quantity)}</span>
          </div>
        ))}
        <div className="total-row">
          <span>Total</span>
          <span>{formatINR(cart.total_paise)}</span>
        </div>

        {error && <div className="msg-error">{error}</div>}

        <button
          className="btn btn-primary"
          style={{ width: "100%" }}
          onClick={pay}
          disabled={busy}
        >
          {busy ? "Processing…" : "Pay with Razorpay"}
        </button>
        <p className="muted" style={{ fontSize: 12, marginTop: 10 }}>
          Test mode: use card 4111 1111 1111 1111, any future date, any CVV.
        </p>
      </div>
    </div>
  );
}
