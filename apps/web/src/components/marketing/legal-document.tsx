import Link from "next/link";

import type { LegalPageContent } from "@/content/site";

type LegalDocumentProps = {
  page: LegalPageContent;
};

export function LegalDocument({ page }: LegalDocumentProps) {
  return (
    <article className="mx-auto max-w-4xl px-6 py-16">
      <header className="border-b border-slate-200 pb-8">
        <p className="text-sm font-medium uppercase tracking-wider text-slate-500">Legal</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 md:text-4xl">
          {page.title}
        </h1>
        <p className="mt-3 max-w-2xl text-slate-600">{page.metaDescription}</p>
        <p className="mt-4 text-sm text-slate-500">Last updated: {page.lastUpdated}</p>
      </header>

      <div className="mt-10 grid gap-12 lg:grid-cols-[220px_1fr]">
        <nav aria-label="Table of contents" className="lg:sticky lg:top-24 lg:self-start">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">On this page</p>
          <ol className="mt-3 space-y-2">
            {page.sections.map((section) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  className="text-sm text-slate-600 transition hover:text-slate-900"
                >
                  {section.title}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <div className="min-w-0 space-y-10">
          {page.sections.map((section) => (
            <section key={section.id} id={section.id} className="scroll-mt-24">
              <h2 className="text-xl font-semibold text-slate-900">{section.title}</h2>
              {section.paragraphs.map((paragraph) => (
                <p key={paragraph.slice(0, 32)} className="mt-3 leading-relaxed text-slate-700">
                  {paragraph}
                </p>
              ))}
              {section.list && section.list.length > 0 && (
                <ul className="mt-3 list-disc space-y-2 pl-5 text-slate-700">
                  {section.list.map((item) => (
                    <li key={item.slice(0, 40)} className="leading-relaxed">
                      {item}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ))}
        </div>
      </div>

      <footer className="mt-16 border-t border-slate-200 pt-8 text-sm text-slate-600">
        <p>
          Questions? See also{" "}
          <Link href="/privacy" className="text-slate-900 underline underline-offset-2">
            Privacy Policy
          </Link>{" "}
          and{" "}
          <Link href="/terms" className="text-slate-900 underline underline-offset-2">
            Terms & Conditions
          </Link>
          .
        </p>
      </footer>
    </article>
  );
}
