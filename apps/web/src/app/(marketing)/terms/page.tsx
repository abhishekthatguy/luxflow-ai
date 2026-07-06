import { JsonLd } from "@/components/marketing/json-ld";
import { LegalDocument } from "@/components/marketing/legal-document";
import { termsPage } from "@/content/site";
import { buildPageMetadata, webPageJsonLd } from "@/lib/seo";

export const metadata = buildPageMetadata({
  title: termsPage.title,
  description: termsPage.metaDescription,
  path: termsPage.path,
  keywords: ["terms of service", "legal software agreement", "acceptable use policy"],
});

export default function TermsPage() {
  return (
    <>
      <JsonLd data={webPageJsonLd(termsPage.title, termsPage.metaDescription, termsPage.path)} />
      <LegalDocument page={termsPage} />
    </>
  );
}
