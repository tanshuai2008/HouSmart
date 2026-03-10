import Link from "next/link";

export default function Home() {
    return (
        <main className="min-h-screen bg-slate-50 flex items-center justify-center px-6">
            <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                <h1 className="text-2xl font-bold text-slate-900">Welcome</h1>
                <p className="mt-2 text-sm text-slate-600">
                    Choose an option to continue.
                </p>

                <div className="mt-6 grid gap-3">
                    <Link
                        href="/auth/login"
                        className="inline-flex h-11 items-center justify-center rounded-lg bg-slate-900 px-4 text-sm font-semibold text-white hover:bg-slate-800"
                    >
                        Login
                    </Link>
                    <Link
                        href="/auth/signup"
                        className="inline-flex h-11 items-center justify-center rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                    >
                        Signup
                    </Link>
                </div>
            </section>
        </main>
    );
}
