"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, formatINR, getToken } from "@/lib/api";

export default function ProductCard({ product }) {
  const router = useRouter();
  const [state, setState] = useState("");

  async function addToCart() {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    if (product.stock < 1) return;
    setState("Adding…");
    try {
      await api("/cart/items", {
        method: "POST",
        body: { product_id: product.id, quantity: 1 },
      });
      setState("Added ✓");
      window.dispatchEvent(new Event("cart-updated"));
      setTimeout(() => setState(""), 1500);
    } catch (e) {
      setState(e.message);
      setTimeout(() => setState(""), 2500);
    }
  }

  return (
    <div className="card product-card">
      <Link href={`/products/${product.slug}`}>
        <img className="product-img" src={product.image_url} alt={product.name} />
        <div className="card-body">
          <span className="muted">{product.category}</span>
          <h3 className="product-name">{product.name}</h3>
          <span className="price">{formatINR(product.price_paise)}</span>
        </div>
      </Link>
      <button
        className="btn btn-primary"
        onClick={addToCart}
        disabled={product.stock < 1 || state === "Adding…"}
      >
        {product.stock < 1 ? "Out of stock" : state || "Add to cart"}
      </button>
    </div>
  );
}
