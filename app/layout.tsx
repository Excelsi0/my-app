import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ExFlow — Revenue Intelligence",
  description:
    "Финансовый радар для агрегации оплаченных операций из нескольких источников.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
