import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VitaRoots — Family Wellness",
  description:
    "AI-powered personalized meal planning, grocery lists, and supplement guidance for every generation of your family.",
  keywords: ["meal planning", "family nutrition", "supplement guide", "wellness", "AI", "VitaRoots"],
  authors: [{ name: "VitaRoots" }],
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "VitaRoots",
  },
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
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <meta name="theme-color" content="#3E6B4A" />
        <link
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-cream antialiased">
        {children}
      </body>
    </html>
  );
}
