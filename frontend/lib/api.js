// Single place every fetch goes through. Adds the JWT from localStorage,
// unwraps FastAPI error bodies (`detail`) into normal Error messages.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("shop_token");
}

export function saveAuth(token) {
  localStorage.setItem("shop_token", token);
  window.dispatchEvent(new Event("auth-changed"));
}

export function clearAuth() {
  localStorage.removeItem("shop_token");
  window.dispatchEvent(new Event("auth-changed"));
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  let data = null;
  try {
    data = await res.json();
  } catch {
    // empty or non-JSON response body
  }

  if (!res.ok) {
    const detail = data?.detail ?? `Request failed (${res.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

// All prices travel over the API as integer paise; format only at render.
export function formatINR(paise) {
  return "₹" + (paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}
