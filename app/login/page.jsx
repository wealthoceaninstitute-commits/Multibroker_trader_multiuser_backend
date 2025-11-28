"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Login() {
  const [email,setEmail] = useState("");
  const [password,setPassword] = useState("");
  const router = useRouter();

  async function login() {
    const res = await fetch("http://localhost:8000/login", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({email,password})
    });

    const data = await res.json();

    if(data.status === "success"){
      localStorage.setItem("user", email);
      router.push("/trade");
    }
    else alert("Invalid credentials");
  }

  return (
    <div style={{maxWidth:400,margin:"100px auto"}}>
      <h2>Login</h2>
      <input onChange={e=>setEmail(e.target.value)} placeholder="Email"/><br/>
      <input type="password" onChange={e=>setPassword(e.target.value)} placeholder="Password"/><br/>
      <button onClick={login}>Login</button>
      <p onClick={()=>router.push('/signup')}>Create Account</p>
    </div>
  )
}
