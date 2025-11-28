// src/lib/apiBase.js

// Base URL for your FastAPI backend.
// Railway will inject NEXT_PUBLIC_API_BASE from your env.
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

// Components (like components/api.js) import this.
export default API_BASE;
