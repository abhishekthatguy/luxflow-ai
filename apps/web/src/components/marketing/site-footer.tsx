import Link from "next/link";

import { footerLinks, siteConfig } from "@/content/site";

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-12 md:grid-cols-4">
        <div className="md:col-span-1">
          <p className="text-lg font-semibold text-slate-900">{siteConfig.name}</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{siteConfig.tagline}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Product</p>
          <ul className="mt-3 space-y-2">
            {footerLinks.product.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="text-sm text-slate-600 hover:text-slate-900">
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Company</p>
          <ul className="mt-3 space-y-2">
            {footerLinks.company.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="text-sm text-slate-600 hover:text-slate-900">
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Contact</p>
          <ul className="mt-3 space-y-2">
            {footerLinks.contact.map((link) => (
              <li key={link.href}>
                <a href={link.href} className="text-sm text-slate-600 hover:text-slate-900">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-100">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-6 py-4 text-xs text-slate-500 sm:flex-row">
          <p>
            © {year} {siteConfig.legalName}. All rights reserved.
          </p>
          <p>Built for enterprise law firms · Attorney judgment first</p>
        </div>
      </div>
    </footer>
  );
}
