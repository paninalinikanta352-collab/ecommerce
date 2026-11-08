"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import ProductCard from "@/components/ProductCard";
import { api } from "@/lib/api";

function ProductsInner() {
  const params = useSearchParams();

  const [qText, setQText] = useState(params.get("q") ?? "");
  const [q, setQ] = useState(params.get("q") ?? "");
  const [category, setCategory] = useState(params.get("category") ?? "");
  const [sort, setSort] = useState("newest");
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState("");

  // debounce the search box so we don't hammer the API on every keystroke
  useEffect(() => {
    const t = setTimeout(() => setQ(qText.trim()), 300);
    return () => clearTimeout(t);
  }, [qText]);

  useEffect(() => {
    api("/products/categories")
      .then(setCategories)
      .catch(() => {});
  }, []);

  useEffect(() => {
    const search = new URLSearchParams();
    if (q) search.set("q", q);
    if (category) search.set("category", category);
    if (sort) search.set("sort", sort);
    api(`/products?${search.toString()}`)
      .then(setProducts)
      .catch((e) => setError(e.message));
  }, [q, category, sort]);

  return (
    <>
      <div className="section-head">
        <h2>All products</h2>
        <span className="muted">{products.length} result(s)</span>
      </div>

      <div className="filters">
        <input
          className="input"
          placeholder="Search products…"
          value={qText}
          onChange={(e) => setQText(e.target.value)}
        />
        <select
          className="input"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select className="input" value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="newest">Newest first</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
        </select>
      </div>

      {error && <div className="msg-error">{error}</div>}

      <div className="grid">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
      {!error && products.length === 0 && (
        <p className="muted">No products match your filters.</p>
      )}
    </>
  );
}

// useSearchParams only works inside a Suspense boundary during static prerender
export default function ProductsPage() {
  return (
    <Suspense fallback={null}>
      <ProductsInner />
    </Suspense>
  );
}
