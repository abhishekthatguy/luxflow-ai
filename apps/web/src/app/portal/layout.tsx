import type { Metadata } from "next";

import { PortalShell } from "@/components/portal-shell";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Client Portal",
  description: "Secure client portal for case updates, documents, and intake.",
};

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <PortalShell>{children}</PortalShell>
    </AuthProvider>
  );
}
