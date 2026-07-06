import { JsonLd } from "@/components/marketing/json-ld";
import { LegalDocument } from "@/components/marketing/legal-document";
import { aboutPage } from "@/content/site";
import { buildPageMetadata, organizationJsonLd, webPageJsonLd } from "@/lib/seo";

export const metadata = buildPageMetadata({
  title: aboutPage.title,
  description: aboutPage.metaDescription,
  path: aboutPage.path,
  keywords: ["about LexFlow AI", "legal tech company", "law firm automation"],
});

export default function AboutPage() {
  return (
    <>
      <JsonLd
        data={[
          organizationJsonLd(),
          webPageJsonLd(aboutPage.title, aboutPage.metaDescription, aboutPage.path),
        ]}
      />
      <LegalDocument page={aboutPage} />
    </>
  );
}
