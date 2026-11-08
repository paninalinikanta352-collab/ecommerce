"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, formatINR, getToken } from "@/lib/api";

const EMPTY_FORM = {
  id: null,
  name: "",
  category: "",
  price: "",
  stock: "",
  image_url: "",
  description: "",
};

export default function AdminPage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function init() {
      if (!getToken()) {
        router.push("/login?next=/admin");
        return;
      }
      try {
        await api("/admin/products"); // 403s if not admin
        setReady(true);
      } catch (e) {
        setError(e.message);
      }
    }
    init();
  }, [router]);

  async function reload() {
    const [p, o] = await Promise.all([api("/admin/products"), api("/admin/orders")]);
    setProducts(p);
    setOrders(o);
  }

  useEffect(() => {
    if (ready) reload().catch((e) => setError(e.message));
  }, [ready]);

  async function saveProduct(e) {
    e.preventDefault();
    setError("");
    const body = {
      name: form.name,
      category: form.category,
      description: form.description,
      image_url: form.image_url,
      price_paise: Math.round(Number(form.price) * 100),
      stock: Number(form.stock),
    };
    try {
      if (form.id) await api(`/admin/products/${form.id}`, { method: "PUT", body });
      else await api("/admin/products", { method: "POST", body });
      setForm(EMPTY_FORM);
      setShowForm(false);
      await reload();
    } catch (err) {
      setError(err.message);
    }
  }

  function startEdit(p) {
    setShowForm(true);
    setForm({
      id: p.id,
      name: p.name,
      category: p.category,
      price: String(p.price_paise / 100),
      stock: String(p.stock),
      image_url: p.image_url,
      description: p.description,
    });
  }

  async function archiveProduct(p) {
    if (!confirm(`Hide "${p.name}" from the store?`)) return;
    try {
      await api(`/admin/products/${p.id}`, { method: "DELETE" });
      await reload();
    } catch (err) {
      setError(err.message);
    }
  }

  async function setOrderStatus(order, status) {
    try {
      await api(`/admin/orders/${order.id}`, { method: "PATCH", body: { status } });
      await reload();
    } catch (err) {
      setError(err.message);
    }
  }

  if (error && !ready) {
    return (
      <div>
        <div className="msg-error">{error}</div>
        <p className="muted">Log in with an admin account to see this page.</p>
      </div>
    );
  }
  if (!ready) return <p className="muted">Loading…</p>;

  return (
    <div>
      <div className="section-head">
        <h2>Admin</h2>
        <div style={{ display: "flex", gap: 10 }}>
          <button
            className="btn btn-primary"
            onClick={() => {
              setShowForm(!showForm);
              setForm(EMPTY_FORM);
            }}
          >
            {showForm ? "Close form" : "+ New product"}
          </button>
        </div>
      </div>

      {error && <div className="msg-error">{error}</div>}

      {showForm && (
        <form className="card" style={{ padding: 18, maxWidth: 520 }} onSubmit={saveProduct}>
          <h3 style={{ margin: "0 0 6px" }}>{form.id ? `Edit product #${form.id}` : "New product"}</h3>

          <label className="label" htmlFor="name">Name</label>
          <input
            id="name"
            className="input"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />

          <label className="label" htmlFor="category">Category</label>
          <input
            id="category"
            className="input"
            required
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          />

          <label className="label" htmlFor="price">Price in ₹ (rupees)</label>
          <input
            id="price"
            className="input"
            type="number"
            min="0.01"
            step="0.01"
            required
            value={form.price}
            onChange={(e) => setForm({ ...form, price: e.target.value })}
          />

          <label className="label" htmlFor="stock">Stock</label>
          <input
            id="stock"
            className="input"
            type="number"
            min="0"
            required
            value={form.stock}
            onChange={(e) => setForm({ ...form, stock: e.target.value })}
          />

          <label className="label" htmlFor="image_url">Image URL</label>
          <input
            id="image_url"
            className="input"
            required
            value={form.image_url}
            onChange={(e) => setForm({ ...form, image_url: e.target.value })}
          />

          <label className="label" htmlFor="description">Description</label>
          <textarea
            id="description"
            className="input"
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />

          <button className="btn btn-primary" style={{ marginTop: 18 }}>
            {form.id ? "Save changes" : "Create product"}
          </button>
        </form>
      )}

      <div className="section-head">
        <h2>All products</h2>
        <span className="muted">{products.length}</span>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Category</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Live</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td>{p.name}</td>
              <td className="muted">{p.category}</td>
              <td>{formatINR(p.price_paise)}</td>
              <td>{p.stock}</td>
              <td>{p.is_active ? "yes" : "hidden"}</td>
              <td style={{ whiteSpace: "nowrap" }}>
                <button className="btn btn-outline" style={{ padding: "5px 10px", marginRight: 6 }} onClick={() => startEdit(p)}>
                  Edit
                </button>
                {p.is_active && (
                  <button className="btn btn-danger" style={{ padding: "5px 10px" }} onClick={() => archiveProduct(p)}>
                    Hide
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="section-head">
        <h2>All orders</h2>
        <span className="muted">{orders.length}</span>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Order</th>
            <th>Customer</th>
            <th>Total</th>
            <th>Items</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td>
                #{o.id}
                <div className="muted" style={{ fontSize: 12 }}>
                  {new Date(o.created_at).toLocaleDateString()}
                </div>
              </td>
              <td>{o.user_email}</td>
              <td>{formatINR(o.total_paise)}</td>
              <td className="muted">
                {o.items.map((i) => `${i.product_name} × ${i.quantity}`).join(", ")}
              </td>
              <td>
                <select
                  className="input"
                  style={{ width: 130 }}
                  value={o.status}
                  onChange={(e) => setOrderStatus(o, e.target.value)}
                >
                  {["created", "paid", "shipped", "delivered", "cancelled"].map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
