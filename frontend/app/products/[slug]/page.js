"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, formatINR, getToken } from "@/lib/api";

export default function ProductDetailPage() {
  const { slug } = useParams();
  const router = useRouter();
  const [product, setProduct] = useState(null);
  const [qty, setQty] = useState(1);
  const [state, setState] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api(`/products/${slug}`)
      .then((p) => {
        setProduct(p);
        if (p.stock > 0) setQty(1);
      })
      .catch((e) => setError(e.message));
  }, [slug]);

  async function addToCart() {
    if (!getToken()) {
      router.push(`/login?next=/products/${slug}`);
      return;
    }
    setState("Adding…");
    try {
      await api("/cart/items", {
        method: "POST",
        body: { product_id: product.id, quantity: Number(qty) },
      });
      setState("Added to cart ✓");
      window.dispatchEvent(new Event("cart-updated"));
      setTimeout(() => setState(""), 1800);
    } catch (e) {
      setState(e.message);
      setTimeout(() => setState(""), 2500);
    }
  }

  if (error) return <div className="msg-error">{error}</div>;
  if (!product) return <p className="muted">Loading…</p>;

  return (
    <div>
      <p>
        <Link className="muted" href="/products">
          ← Back to products
        </Link>
      </p>

      <div className="detail-layout">
        <img
          className="card"
          src={product.image_url}
          alt={product.name}
          style={{ aspectRatio: "1", objectFit: "cover" }}
        />

        <div>
          <span className="muted">{product.category}</span>
          <h1 style={{ margin: "4px 0 10px", fontSize: 28 }}>{product.name}</h1>
          <p className="price" style={{ fontSize: 22 }}>
            {formatINR(product.price_paise)}
          </p>

          <p>{product.description}</p>

          <p className="muted">
            {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
          </p>

          {product.stock > 0 && (
            <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 16 }}>
              <select
                className="input"
                style={{ width: 80 }}
                value={qty}
                onChange={(e) => setQty(e.target.value)}
              >
                {Array.from({ length: Math.min(product.stock, 10) }, (_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {i + 1}
                  </option>
                ))}
              </select>
              <button
                className="btn btn-primary"
                onClick={addToCart}
                disabled={state === "Adding…"}
              >
                {state || "Add to cart"}
              </button>
              <Link className="btn btn-outline" href="/cart">
                Go to cart
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
