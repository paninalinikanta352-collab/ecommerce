"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProductCard from "@/components/ProductCard";
import { api } from "@/lib/api";

export default function HomePage() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/products?sort=newest")
      .then((data) => setProducts(data.slice(0, 8)))
      .catch((e) => setError(e.message));
  }, []);

  return (
    <>
      <section className="hero">
        <h1>Things worth buying, honestly listed.</h1>
        <p>
          Electronics, fashion, home and fitness — shipped across India, paid securely
          through Razorpay.
        </p>
      </section>

      {error && <div className="msg-error">{error}</div>}

      <div className="section-head">
        <h2>New arrivals</h2>
        <Link className="btn btn-outline" href="/products">
          View all products
        </Link>
      </div>

      <div className="grid">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </>
  );
}
