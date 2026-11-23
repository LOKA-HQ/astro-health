// API client for the Astro Health backend. The base URL comes from the
// VITE_API_BASE environment variable and defaults to the local dev server.
export const API = (import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1').replace(
  /\/$/,
  '',
);

// GET a JSON resource, throwing on any non-2xx response.
export async function get(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw Error(`${r.status} ${r.statusText}`);
  return r.json();
}
