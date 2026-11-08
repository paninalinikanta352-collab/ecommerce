"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearAuth, getToken } from "@/lib/api";

export default function Navbar() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [count, setCount] = useState(0);

  async function refresh() {
    if (!getToken()) {
      setUser(null);
      setCount(0);
      return;
    }
    try {
      const [me, cart] = await Promise.all([api("/auth/me"), api("/cart")]);
      setUser(me);
      setCount(cart.items.reduce((n, item) => n + item.quantity, 0));
    } catch {
      // token is dead — drop it and render as logged out
      clearAuth();
      setUser(null);
      setCount(0);
    }
  }

  useEffect(() => {
    refresh();
    const onChange = () => refresh();
    window.addEventListener("cart-updated", onChange);
    window.addEventListener("auth-changed", onChange);
    return () => {
      window.removeEventListener("cart-updated", onChange);
      window.removeEventListener("auth-changed", onChange);
    };
  }, []);

  async function handleLogout() {
    clearAuth();
    setUser(null);
    router.push("/");
  }

  return (
    <header className="nav">
      <div className="nav-inner container">
        <Link href="/" className="brand">
          MyShop
        </Link>
        <Link href="/products">Products</Link>
        <div className="nav-spacer" />
        {user?.is_admin && <Link href="/admin">Admin</Link>}
        {user && <Link href="/orders">My orders</Link>}
        {user ? (
          <button onClick={handleLogout}>Logout</button>
        ) : (
          <Link href="/login">Login</Link>
        )}
        <Link href="/cart" className="cart-link">
          Cart{count > 0 ? ` (${count})` : ""}
        </Link>
      </div>
    </header>
  );
}
