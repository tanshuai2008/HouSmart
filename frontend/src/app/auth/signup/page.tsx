import { AuthLayout } from "@/components/auth/AuthLayout";
import { RegistrationForm } from "@/components/auth/RegistrationForm";

export default function SignUpPage() {
    return (
        <AuthLayout>
            <RegistrationForm />
        </AuthLayout>
    );
}
