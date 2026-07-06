import Link from "next/link";

import { JsonLd } from "@/components/marketing/json-ld";
import {
  capabilities,
  howItWorks,
  siteConfig,
  trustPoints,
} from "@/content/site";
import {
  buildPageMetadata,
  faqJsonLd,
  organizationJsonLd,
  softwareApplicationJsonLd,
  websiteJsonLd,
} from "@/lib/seo";

export const metadata = buildPageMetadata({
  title: siteConfig.name,
  description: siteConfig.description,
  path: "/",
  keywords: [
    "enterprise legal software",
    "law firm automation",
    "AI case summaries",
    "legal document OCR",
    "matter wall software",
  ],
});

const faqs = [
  {
    question: "Does LexFlow AI replace attorneys?",
    answer:
      "No. LexFlow AI automates repetitive tasks — intake, document processing, workflow routing — while every AI output requires attorney review before client or court delivery.",
  },
  {
    question: "How does LexFlow AI handle confidentiality and ethical walls?",
    answer:
      "Matter walls enforce case-scoped access at the API layer. Unauthorized users receive 404 responses. All mutating actions are written to immutable audit logs.",
  },
  {
    question: "What AI provider does LexFlow AI use?",
    answer:
      "Production deployments use Azure OpenAI under firm-configured policies. Local development uses a stub provider. Document text never leaves firm-scoped boundaries without explicit configuration.",
  },
  {
    question: "Can LexFlow AI integrate with Microsoft 365?",
    answer:
      "Yes. Phase 2 includes Entra ID authentication, Outlook, SharePoint, and Teams notifications. n8n orchestrates external calls while FastAPI owns business logic.",
  },
];

export default function LandingPage() {
  return (
    <>
      <JsonLd
        data={[
          organizationJsonLd(),
          websiteJsonLd(),
          softwareApplicationJsonLd(),
          faqJsonLd(faqs),
        ]}
      />

      {/* Hero */}
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-20 md:py-28">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-wider text-slate-500">
              Enterprise legal automation
            </p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-900 md:text-5xl md:leading-tight">
              Automate legal work.
              <span className="block text-slate-600">Preserve attorney judgment.</span>
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-slate-600">{siteConfig.description}</p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href="/login"
                className="rounded-md bg-slate-900 px-6 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
              >
                Sign in to platform
              </Link>
              <Link
                href="/about"
                className="rounded-md border border-slate-300 bg-white px-6 py-3 text-sm font-medium text-slate-800 transition hover:bg-slate-50"
              >
                About LexFlow AI
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section id="capabilities" className="mx-auto max-w-6xl px-6 py-20">
        <div className="max-w-2xl">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 md:text-3xl">
            Everything your firm needs in one platform
          </h2>
          <p className="mt-3 text-slate-600">
            Purpose-built for litigation, corporate, and regulatory practices at firms with 500–2,000+
            attorneys — not a generic CRM with legal branding.
          </p>
        </div>
        <ul className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((cap) => (
            <li
              key={cap.title}
              className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-slate-300"
            >
              <span className="text-2xl" aria-hidden="true">
                {cap.icon}
              </span>
              <h3 className="mt-3 font-semibold text-slate-900">{cap.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{cap.description}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Security */}
      <section id="security" className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-slate-900 md:text-3xl">
                Security and compliance by design
              </h2>
              <p className="mt-3 leading-relaxed text-slate-600">
                LexFlow AI is built for firms that cannot afford data leaks, silent AI errors, or
                unaudited access. Every architectural decision — matter walls, private n8n, structured
                logging with PII redaction — reflects that reality.
              </p>
            </div>
            <ul className="grid gap-3 sm:grid-cols-2">
              {trustPoints.map((point) => (
                <li
                  key={point}
                  className="flex items-start gap-2 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-700"
                >
                  <span className="mt-0.5 text-green-600" aria-hidden="true">
                    ✓
                  </span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 md:text-3xl">
          How it works
        </h2>
        <ol className="mt-12 grid gap-8 md:grid-cols-3">
          {howItWorks.map((item) => (
            <li key={item.step} className="relative">
              <span className="text-4xl font-bold text-slate-200">{item.step}</span>
              <h3 className="mt-2 text-lg font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{item.description}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* FAQ */}
      <section id="faq" className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-3xl px-6 py-20">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
            Frequently asked questions
          </h2>
          <dl className="mt-10 space-y-8">
            {faqs.map((faq) => (
              <div key={faq.question}>
                <dt className="font-medium text-slate-900">{faq.question}</dt>
                <dd className="mt-2 text-sm leading-relaxed text-slate-600">{faq.answer}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-slate-200 bg-slate-900">
        <div className="mx-auto max-w-6xl px-6 py-16 text-center">
          <h2 className="text-2xl font-semibold text-white md:text-3xl">
            Ready to modernize your firm&apos;s workflows?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-slate-300">
            Join firms reducing intake time by 60% while maintaining full audit defensibility.
          </p>
          <Link
            href="/login"
            className="mt-8 inline-block rounded-md bg-white px-6 py-3 text-sm font-medium text-slate-900 transition hover:bg-slate-100"
          >
            Access the platform
          </Link>
        </div>
      </section>
    </>
  );
}
