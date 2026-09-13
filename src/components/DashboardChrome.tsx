"use client";

import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

export default function DashboardChrome({ children }: { children: ReactNode }) {
  const isDashboard = usePathname() === "/dashboard";
  if (isDashboard) return <>{children}</>;
  return <><Header /><div className="min-h-screen max-w-screen-d mx-auto px-4">{children}</div><Footer /></>;
}
