import { AuthLayout } from "@/components/layout/AuthLayout";
import { SignUpForm } from "@/components/auth/SignUpForm";

export default function SignUpPage() {
    return (
        <AuthLayout>
            <SignUpForm />
        </AuthLayout>
    );
}
