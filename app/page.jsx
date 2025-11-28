"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_BASE;

export default function Home() {
  const router = useRouter();

  const [tab, setTab] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");

  const login = async () => {
    setMsg("Logging in...");

    try {
      const res = await fetch(`${API}/users/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (!res.ok) {
        setMsg(data.detail || "Login failed");
        return;
      }

      localStorage.setItem("auth", "true");
      localStorage.setItem("user", username);

      router.replace("/trader");
    } catch (e) {
      setMsg("Backend not reachable");
    }
  };

  const createUser = async () => {
    setMsg("Creating user...");

    try {
      const res = await fetch(`${API}/users/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (!res.ok) {
        setMsg(data.detail || "User already exists");
        return;
      }

      setMsg("✅ User created. Now login.");
      setTab("login");
    } catch (e) {
      setMsg("Backend not reachable");
    }
  };

  return (
    <div style={{ maxWidth: 420, margin: "80px auto", fontFamily: "Arial" }}>
      <h1 style={{ textAlign: "center" }}>Wealth Ocean – Login</h1>
      <p style={{ textAlign: "center", color: "#666" }}>
        Multi-broker, multi-user trading panel
      </p>

      {msg && (
        <div style={{ background: "#fee", padding: 10, margin: "10px 0" }}>
          {msg}
        </div>
      )}

      <div style={{ display: "flex", marginBottom: 20 }}>
        <button
          onClick={() => setTab("login")}
          style={{
            flex: 1,
            padding: 10,
            background: tab === "login" ? "#000" : "#eee",
            color: tab === "login" ? "#fff" : "#000"
          }}
        >
          Login
        </button>

        <button
          onClick={() => setTab("create")}
          style={{
            flex: 1,
            padding: 10,
            background: tab === "create" ? "#000" : "#eee",
            color: tab === "create" ? "#fff" : "#000"
          }}
        >
          Create User
        </button>
      </div>

      <input
        placeholder="User ID"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        style={{ width: "100%", padding: 10, marginBottom: 10 }}
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={{ width: "100%", padding: 10, marginBottom: 20 }}
      />

      {tab === "login" ? (
        <button
          onClick={login}
          style={{ width: "100%", padding: 12, background: "#2563eb", color: "#fff" }}
        >
          Login
        </button>
      ) : (
        <button
          onClick={createUser}
          style={{ width: "100%", padding: 12, background: "#16a34a", color: "#fff" }}
        >
          Create User
        </button>
      )}
    </div>
  );
}
