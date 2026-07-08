import { PortalHome } from "@/components/portal-home";

type PortalHomePageProps = {
  searchParams?: { name?: string; email?: string };
};

export default function PortalHomePage({ searchParams }: PortalHomePageProps) {
  return (
    <PortalHome
      clientName={searchParams?.name?.trim()}
      clientEmail={searchParams?.email?.trim()}
    />
  );
}
