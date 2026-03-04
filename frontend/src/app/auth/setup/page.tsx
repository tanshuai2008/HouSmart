import { redirect } from "next/navigation";

export default function SetupRedirect() {
    redirect("/auth/setup/role");
}
