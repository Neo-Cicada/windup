import type { Metadata } from "next";
import { Fredoka, Nunito } from "next/font/google";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const fredoka = Fredoka({
  variable: "--font-fredoka",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: "Windup Academy — Ace your coding interview, one toy at a time",
  description:
    "A secret training academy run by toys. Fix broken gadgets, climb the shelves, battle boss toys, and earn merit badges while mastering real data-structure and algorithm patterns.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${fredoka.variable} ${nunito.variable}`}>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
