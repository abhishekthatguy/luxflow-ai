import type { MetadataRoute } from "next";

import { legalPages, siteConfig } from "@/content/site";
import { absoluteUrl } from "@/lib/seo";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const staticRoutes = ["", ...legalPages.map((p) => p.path.replace(/^\//, ""))];

  return staticRoutes.map((route) => ({
    url: absoluteUrl(route ? `/${route}` : "/"),
    lastModified: now,
    changeFrequency: route === "" ? "weekly" : "monthly",
    priority: route === "" ? 1 : 0.7,
  }));
}
