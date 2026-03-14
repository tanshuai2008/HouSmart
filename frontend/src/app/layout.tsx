import type { Metadata } from "next";
import { AuthProvider } from "@/providers/auth-context";
import logoIconV2 from "@/assets/icons/logo-icon-v2.svg";
import "./globals.css";

export const metadata: Metadata = {
  title: "HouSmart",
  description: "The intelligent decision engine for real estate.",
  icons: {
    icon: logoIconV2.src,
    shortcut: logoIconV2.src,
    apple: logoIconV2.src,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="overflow-y-scroll" suppressHydrationWarning>
      <body className="font-sans antialiased" suppressHydrationWarning>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
