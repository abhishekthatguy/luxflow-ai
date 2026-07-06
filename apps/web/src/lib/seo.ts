import type { Metadata } from "next";

import { siteConfig } from "@/content/site";

type PageMetaInput = {
  title: string;
  description: string;
  path?: string;
  keywords?: string[];
  noIndex?: boolean;
};

export function absoluteUrl(path = ""): string {
  const base = siteConfig.url.replace(/\/$/, "");
  const suffix = path.startsWith("/") ? path : path ? `/${path}` : "";
  return `${base}${suffix}`;
}

export function buildPageMetadata({
  title,
  description,
  path = "",
  keywords = [],
  noIndex = false,
}: PageMetaInput): Metadata {
  const url = absoluteUrl(path);
  const fullTitle = path === "" || path === "/" ? `${siteConfig.name} — ${siteConfig.tagline}` : `${title} | ${siteConfig.name}`;

  return {
    title: fullTitle,
    description,
    keywords: [
      "legal automation",
      "law firm software",
      "case management",
      "legal AI",
      "document automation",
      "matter management",
      ...keywords,
    ],
    authors: [{ name: siteConfig.legalName, url: siteConfig.url }],
    creator: siteConfig.legalName,
    publisher: siteConfig.legalName,
    metadataBase: new URL(siteConfig.url),
    alternates: { canonical: url },
    openGraph: {
      type: path === "" || path === "/" ? "website" : "article",
      locale: siteConfig.locale,
      url,
      siteName: siteConfig.name,
      title: fullTitle,
      description,
    },
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description,
    },
    robots: noIndex
      ? { index: false, follow: false }
      : { index: true, follow: true, googleBot: { index: true, follow: true } },
  };
}

export function organizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: siteConfig.legalName,
    url: siteConfig.url,
    logo: absoluteUrl("/logo.png"),
    description: siteConfig.description,
    foundingDate: String(siteConfig.foundedYear),
    email: siteConfig.supportEmail,
    address: {
      "@type": "PostalAddress",
      streetAddress: siteConfig.address.street,
      addressLocality: siteConfig.address.city,
      addressRegion: siteConfig.address.region,
      postalCode: siteConfig.address.postalCode,
      addressCountry: siteConfig.address.country,
    },
    sameAs: [],
  };
}

export function websiteJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: siteConfig.name,
    url: siteConfig.url,
    description: siteConfig.description,
    publisher: { "@type": "Organization", name: siteConfig.legalName },
  };
}

export function webPageJsonLd(title: string, description: string, path: string) {
  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: title,
    description,
    url: absoluteUrl(path),
    isPartOf: { "@type": "WebSite", name: siteConfig.name, url: siteConfig.url },
    inLanguage: "en-US",
  };
}

export function softwareApplicationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: siteConfig.name,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description: siteConfig.description,
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
      description: "Enterprise pricing — contact for quote",
    },
    provider: { "@type": "Organization", name: siteConfig.legalName },
  };
}

export function faqJsonLd(items: { question: string; answer: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer },
    })),
  };
}
