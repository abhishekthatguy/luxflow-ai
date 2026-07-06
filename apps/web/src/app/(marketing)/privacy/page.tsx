import { JsonLd } from "@/components/marketing/json-ld";
import { LegalDocument } from "@/components/marketing/legal-document";
import { privacyPage } from "@/content/site";
import { buildPageMetadata, webPageJsonLd } from "@/lib/seo";

export const metadata = buildPageMetadata({
  title: privacyPage.title,
  description: privacyPage.metaDescription,
  path: privacyPage.path,
  keywords: ["privacy policy", "legal software data protection", "GDPR", "CCPA"],
});

export default function PrivacyPage() {
  return (
    <>
      <JsonLd data={webPageJsonLd(privacyPage.title, privacyPage.metaDescription, privacyPage.path)} />
      <LegalDocument page={privacyPage} />
    </>
  );
}
