"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const API = process.env.NEXT_PUBLIC_API_BASE;

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API}/users/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password: password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          data?.detail || data?.message || "Invalid login credentials"
        );
      }

      // Save token & user
      localStorage.setItem("token", data.token);
      localStorage.setItem("username", data.username);

      alert("✅ Login Successful");

      // Redirect after login
      router.push("/");
    } catch (err) {
      alert("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#030b2f] via-[#061955] to-[#020815] flex items-center justify-center">
      <div className="bg-white p-10 rounded-xl shadow-2xl w-[400px]">
        <h1 className="text-3xl font-bold text-center mb-6">Login</h1>

        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <input
            type="password"
            placeholder="Password"
            className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-700 text-white p-3 rounded hover:bg-blue-800 transition-all"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm">
          Don’t have an account?{" "}
          <a
            href="/signup"
            className="text-blue-700 font-semibold hover:underline"
          >
            Create new account
          </a>
        </p>
      </div>
    </div>
  );
}
