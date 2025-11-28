"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

export default function Signup() {
  const [name, setName] = useState("");
  const [email,setEmail] = useState("");
  const [password,setPassword] = useState("");
  const router = useRouter();

  async function signup() {
    if (!name || !email || !password) {
      alert("All fields required");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/users/register`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ name, email, password })
      });

      const data = await res.json();

      if (res.ok) {
        alert("✅ User Created Successfully");
        router.push("/login");
      } else {
        alert(data.detail || data.message || "Signup failed");
      }

    } catch (err) {
      console.error(err);
      alert("❌ Server not reachable");
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>

        <h2 style={styles.title}>Create User</h2>

        <input
          style={styles.input}
          placeholder="Full Name"
          onChange={e=>setName(e.target.value)}
        />

        <input
          style={styles.input}
          placeholder="Email"
          type="email"
          onChange={e=>setEmail(e.target.value)}
        />

        <input
          style={styles.input}
          placeholder="Password"
          type="password"
          onChange={e=>setPassword(e.target.value)}
        />

        <button 
          style={styles.btn}
          onClick={signup}
        >
          Create Account
        </button>

        <p
          style={styles.link}
          onClick={()=>router.push("/login")}
        >
          Already have account? Login
        </p>

      </div>
    </div>
  );
}

const styles = {
  page:{
    display:"flex",
    justifyContent:"center",
    alignItems:"center",
    height:"100vh",
    background:"linear-gradient(135deg, #0f172a, #1e3a8a)"
  },

  card:{
    width:350,
    background:"white",
    padding:30,
    borderRadius:12,
    boxShadow:"0 20px 40px rgba(0,0,0,0.3)",
    textAlign:"center"
  },

  title:{
    marginBottom:20
  },

  input:{
    width:"100%",
    padding:"12px",
    marginBottom:15,
    borderRadius:8,
    border:"1px solid #ccc",
    outline:"none",
    fontSize:14
  },

  btn:{
    width:"100%",
    padding:"12px",
    background:"#1e40af",
    color:"white",
    border:"none",
    borderRadius:8,
    cursor:"pointer",
    fontWeight:"bold"
  },

  link:{
    marginTop:15,
    cursor:"pointer",
    color:"#1e40af"
  }
};
