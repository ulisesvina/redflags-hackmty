import type { Metadata } from "next";
import "@/styles/globals.css";
import "@/styles/dashboard.css";
import DashboardChrome from "@/components/DashboardChrome";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "RedFlags",
  description: "Evidence-backed financial investigations.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col gap-10 justify-between">
        <DashboardChrome>{children}</DashboardChrome>
      </body>
    </html>
  );
}
