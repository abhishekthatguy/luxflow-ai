import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LexFlow AI",
  description: "Enterprise AI automation for law firms",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
