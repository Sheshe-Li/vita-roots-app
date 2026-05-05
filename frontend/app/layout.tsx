import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VitaRoots — Intelligent Family Nutrition",
  description:
    "AI-powered personalized meal planning, grocery lists, and supplement guidance for every generation of your family.",
  keywords: ["meal planning", "family nutrition", "supplement guide", "wellness", "AI", "VitaRoots"],
  authors: [{ name: "VitaRoots" }],
  openGraph: {
    title: "VitaRoots — Intelligent Family Nutrition",
    description: "One plan. Every age. Every need.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="min-h-screen bg-cream antialiased">
        {children}
      </body>
    </html>
  );
}
