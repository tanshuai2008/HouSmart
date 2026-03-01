import { redirect } from "next/navigation";

export default function Home() {
  // Redirect to login page for now as it's the only page available
  redirect("/login");
}
