import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@/providers/auth-context";
import logoIconV2 from "@/assets/icons/logo-icon-v2.svg";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

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
      <body
        className={`${inter.variable} font-sans antialiased`}
        suppressHydrationWarning
      >
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
