import type { Metadata } from "next";

import { PortalShell } from "@/components/portal-shell";

export const metadata: Metadata = {
  title: "Client Portal",
  description: "Secure client portal for case updates, documents, and intake.",
};

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  return <PortalShell>{children}</PortalShell>;
}
