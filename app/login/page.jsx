"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

  const handleLogin = async () => {
    if (!email || !password) {
      alert("Enter email and password");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/users/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email: email.toLowerCase(),   // ✅ REQUIRED
          password: password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Login failed");
        return;
      }

      // Save token and user
      localStorage.setItem("token", data.token);
      localStorage.setItem("username", data.username);

      alert("✅ Login Success");

      // Go to trade
      router.push("/trade");

    } catch (err) {
      console.error(err);
      alert("Server not reachable");
    }
  };

  return (
    <div style={{ padding: "30px" }}>
      <h1>Login</h1>

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        style={{ marginRight: "10px", padding: "6px" }}
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={{ marginRight: "10px", padding: "6px" }}
      />

      <button onClick={handleLogin}>
        Login
      </button>

      <p style={{ marginTop: "20px" }}>
        Don’t have an account?{" "}
        <a href="/signup">Create new account</a>
      </p>
    </div>
  );
}
