import { redirect } from "next/navigation";

export default function Home() {
  // Always send to login page
  redirect("/login");
}
