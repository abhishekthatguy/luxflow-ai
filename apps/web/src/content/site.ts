/** Central site configuration — single source for SEO and legal page generation. */

export const siteConfig = {
  name: "LexFlow AI",
  legalName: "LexFlow AI, Inc.",
  tagline: "Enterprise AI automation for law firms",
  description:
    "LexFlow AI is a production-grade legal automation platform for US law firms. Automate case intake, document processing, AI-assisted summaries, workflow orchestration, and compliance-grade audit trails — without replacing attorney judgment.",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://lexflow.ai",
  locale: "en_US",
  contactEmail: "privacy@lexflow.ai",
  supportEmail: "support@lexflow.ai",
  address: {
    street: "1200 Legal Technology Way, Suite 400",
    city: "Atlanta",
    region: "GA",
    postalCode: "30309",
    country: "United States",
  },
  foundedYear: 2026,
} as const;

export const navLinks = [
  { href: "/#capabilities", label: "Capabilities" },
  { href: "/#security", label: "Security" },
  { href: "/about", label: "About" },
] as const;

export const footerLinks = {
  product: [
    { href: "/#capabilities", label: "Capabilities" },
    { href: "/#how-it-works", label: "How it works" },
    { href: "/login", label: "Sign in" },
  ],
  company: [
    { href: "/about", label: "About us" },
    { href: "/privacy", label: "Privacy policy" },
    { href: "/terms", label: "Terms & conditions" },
  ],
  contact: [
    { href: `mailto:${siteConfig.supportEmail}`, label: siteConfig.supportEmail },
  ],
} as const;

export type Capability = {
  title: string;
  description: string;
  icon: string;
};

export const capabilities: Capability[] = [
  {
    title: "Case & matter management",
    description:
      "Central hub for clients, timelines, tasks, deadlines, and hearings. Matter walls enforce ethical and conflict boundaries with 404-deny semantics.",
    icon: "⚖️",
  },
  {
    title: "Document pipeline",
    description:
      "Presigned S3 uploads, virus scanning, OCR extraction, version control, and semantic search — linked to cases with full audit trails.",
    icon: "📄",
  },
  {
    title: "AI-assisted summaries",
    description:
      "Async case and document summaries with human-in-the-loop approval. Attorneys review every output before it reaches clients or courts.",
    icon: "✨",
  },
  {
    title: "Workflow automation",
    description:
      "Event-driven orchestration via n8n for notifications, intake routing, and external integrations. FastAPI owns all business decisions.",
    icon: "⚙️",
  },
  {
    title: "Compliance & audit",
    description:
      "Immutable audit logs for every significant action. Searchable by case, user, and resource. Retained per firm policy (default 7 years).",
    icon: "🔒",
  },
  {
    title: "Enterprise notifications",
    description:
      "In-app, email, and Microsoft Teams alerts for deadlines, approvals, task assignments, and workflow completions.",
    icon: "🔔",
  },
];

export const trustPoints = [
  "SOC 2 Type II aligned controls (in progress)",
  "Matter walls with ethical-wall enforcement",
  "PII redaction in structured logs",
  "Azure OpenAI with firm-scoped data boundaries",
  "No public n8n exposure — private network only",
  "100% mutating API calls audit-logged",
];

export const howItWorks = [
  {
    step: "01",
    title: "Connect your firm",
    description:
      "Provision users via Entra ID, assign roles (Attorney, Paralegal, Managing Partner), and configure matter walls and practice areas.",
  },
  {
    step: "02",
    title: "Automate the work",
    description:
      "Upload documents, trigger AI summaries, and run workflow automations. Celery workers and n8n handle async processing at scale.",
  },
  {
    step: "03",
    title: "Review & deliver",
    description:
      "Attorneys approve AI outputs, track deadlines on unified timelines, and export audit-ready reports for compliance officers.",
  },
];

export type LegalSection = {
  id: string;
  title: string;
  paragraphs: string[];
  list?: string[];
};

export type LegalPageContent = {
  slug: string;
  path: string;
  title: string;
  metaDescription: string;
  lastUpdated: string;
  sections: LegalSection[];
};

export const aboutPage: LegalPageContent = {
  slug: "about",
  path: "/about",
  title: "About LexFlow AI",
  metaDescription:
    "LexFlow AI builds enterprise legal automation for US law firms — case management, document AI, workflow orchestration, and compliance-grade audit trails.",
  lastUpdated: "2026-07-06",
  sections: [
    {
      id: "mission",
      title: "Our mission",
      paragraphs: [
        "LexFlow AI exists to eliminate repetitive manual work in large law firms — not to replace legal judgment. We augment attorneys, paralegals, and operations teams with a unified platform for case intake, document processing, AI-assisted research and summarization, and defensible audit trails.",
        "Every feature is designed for firms with 500–2,000+ attorneys: high document volume, strict confidentiality, ethical walls, and Microsoft 365 ecosystems.",
      ],
    },
    {
      id: "what-we-build",
      title: "What we build",
      paragraphs: [
        "LexFlow AI is a production-grade platform deployed inside your firm's security boundary. FastAPI powers business logic and persistence; Celery handles async document and AI jobs; n8n orchestrates external notifications and integrations without direct database access.",
      ],
      list: [
        "Case and client management with matter-wall enforcement",
        "Secure document upload, OCR, and full-text search",
        "Human-in-the-loop AI summaries and research drafts",
        "Workflow automation with approval chains",
        "Immutable audit logs and compliance reporting",
      ],
    },
    {
      id: "who-we-serve",
      title: "Who we serve",
      paragraphs: [
        "We serve litigation, corporate, and regulatory practices at firms comparable to Freeman Mathis & Gary LLP — multi-office organizations that need enterprise security, scalability, and integration with existing billing and DMS systems.",
      ],
    },
    {
      id: "values",
      title: "Our values",
      paragraphs: [],
      list: [
        "Attorney judgment first — AI outputs are drafts, never auto-filed or auto-sent",
        "Security by design — private networks, encryption at rest and in transit, least-privilege RBAC",
        "Audit everything — if it mutates state, it is logged",
        "Transparency — clear data handling, retention, and subprocessors in our Privacy Policy",
      ],
    },
    {
      id: "contact",
      title: "Contact",
      paragraphs: [
        `${siteConfig.legalName}`,
        `${siteConfig.address.street}, ${siteConfig.address.city}, ${siteConfig.address.region} ${siteConfig.address.postalCode}`,
        `General inquiries: ${siteConfig.supportEmail}`,
        `Privacy requests: ${siteConfig.contactEmail}`,
      ],
    },
  ],
};

export const privacyPage: LegalPageContent = {
  slug: "privacy",
  path: "/privacy",
  title: "Privacy Policy",
  metaDescription:
    "LexFlow AI Privacy Policy — how we collect, use, store, and protect personal data for law firm users, clients, and document processing.",
  lastUpdated: "2026-07-06",
  sections: [
    {
      id: "introduction",
      title: "1. Introduction",
      paragraphs: [
        `${siteConfig.legalName} ("LexFlow AI," "we," "us") provides enterprise legal automation software to law firms ("Customers," "Firms"). This Privacy Policy describes how we process personal data when you visit our website, use our platform, or interact with our services.`,
        "We process data as a processor on behalf of Firms for matter-related content, and as a controller for account, billing, and website analytics data. Firms remain responsible for client confidentiality obligations under applicable rules of professional conduct.",
      ],
    },
    {
      id: "data-we-collect",
      title: "2. Data we collect",
      paragraphs: ["We collect the following categories of information:"],
      list: [
        "Account data: name, email, firm affiliation, role assignments, authentication logs",
        "Case and matter data: client names, case metadata, documents, notes, timelines (provided by the Firm)",
        "Usage data: feature interactions, API requests, audit logs, error diagnostics",
        "Technical data: IP address, browser type, device identifiers, cookies (see Section 8)",
        "AI processing data: document text sent to LLM providers under Firm-configured policies",
      ],
    },
    {
      id: "how-we-use",
      title: "3. How we use data",
      paragraphs: ["We use personal data to:"],
      list: [
        "Provide, maintain, and improve the LexFlow AI platform",
        "Authenticate users and enforce role-based access and matter walls",
        "Process documents, generate AI summaries, and run workflow automations",
        "Maintain immutable audit logs for compliance and security investigations",
        "Send service notifications (deadlines, approvals, system alerts)",
        "Comply with legal obligations and respond to lawful requests",
      ],
    },
    {
      id: "legal-bases",
      title: "4. Legal bases (EEA/UK)",
      paragraphs: [
        "Where GDPR applies, we rely on: (a) contract performance for platform delivery; (b) legitimate interests for security, fraud prevention, and product improvement; (c) consent where required for non-essential cookies; and (d) legal obligation where applicable.",
      ],
    },
    {
      id: "sharing",
      title: "5. Sharing and subprocessors",
      paragraphs: [
        "We do not sell personal data. We share data with infrastructure and service providers necessary to operate the platform, including cloud hosting (AWS), identity providers (Microsoft Entra ID), email delivery (AWS SES), and AI inference (Azure OpenAI) when enabled by the Firm.",
        "All subprocessors are bound by data processing agreements with security and confidentiality obligations equivalent to this Policy.",
      ],
    },
    {
      id: "retention",
      title: "6. Retention",
      paragraphs: [
        "Audit logs are retained per Firm policy (default 7 years). Case and document data is retained while the Firm maintains an active subscription and as required by Firm-configured policies. Website analytics are retained for 26 months unless deleted earlier.",
        "Upon contract termination, Firms may export data during a defined transition window; thereafter data is deleted or anonymized per the Data Processing Addendum.",
      ],
    },
    {
      id: "security",
      title: "7. Security",
      paragraphs: [
        "We implement encryption in transit (TLS 1.2+) and at rest (AES-256), network segmentation, least-privilege access, structured logging with PII redaction, vulnerability scanning, and annual penetration testing. Matter walls prevent cross-case data access at the application layer.",
      ],
    },
    {
      id: "cookies",
      title: "8. Cookies and tracking",
      paragraphs: [
        "Our marketing site uses essential cookies for session management. Analytics cookies, if enabled, help us understand aggregate traffic patterns. You may control non-essential cookies through your browser settings or our cookie preferences banner when available.",
      ],
    },
    {
      id: "your-rights",
      title: "9. Your rights",
      paragraphs: [
        "Depending on jurisdiction, you may have rights to access, correct, delete, restrict, or port your personal data, and to object to certain processing. Firm users should contact their Firm administrator first; individuals may contact us at the address below.",
        "California residents may have additional rights under CCPA/CPRA. We do not sell personal information.",
      ],
    },
    {
      id: "children",
      title: "10. Children's privacy",
      paragraphs: [
        "LexFlow AI is a B2B platform not directed to individuals under 16. We do not knowingly collect data from children.",
      ],
    },
    {
      id: "changes",
      title: "11. Changes to this policy",
      paragraphs: [
        "We may update this Privacy Policy periodically. Material changes will be posted on this page with an updated effective date. Continued use after changes constitutes acceptance where permitted by law.",
      ],
    },
    {
      id: "contact",
      title: "12. Contact us",
      paragraphs: [
        `Privacy inquiries: ${siteConfig.contactEmail}`,
        `${siteConfig.legalName}, ${siteConfig.address.street}, ${siteConfig.address.city}, ${siteConfig.address.region} ${siteConfig.address.postalCode}, ${siteConfig.address.country}`,
      ],
    },
  ],
};

export const termsPage: LegalPageContent = {
  slug: "terms",
  path: "/terms",
  title: "Terms & Conditions",
  metaDescription:
    "LexFlow AI Terms and Conditions — service agreement, acceptable use, disclaimers, and limitations for enterprise legal automation software.",
  lastUpdated: "2026-07-06",
  sections: [
    {
      id: "agreement",
      title: "1. Agreement to terms",
      paragraphs: [
        `These Terms & Conditions ("Terms") govern access to and use of the LexFlow AI platform and website operated by ${siteConfig.legalName}. By accessing our services, you agree to these Terms and our Privacy Policy.`,
        "If you use the platform on behalf of a law firm, you represent that you have authority to bind that organization. Firm-wide subscriptions are governed by the Master Services Agreement (MSA) and Data Processing Addendum (DPA), which prevail over these Terms in case of conflict.",
      ],
    },
    {
      id: "service",
      title: "2. Description of service",
      paragraphs: [
        "LexFlow AI provides software for case management, document processing, AI-assisted summarization, workflow automation, and audit logging for legal professionals. The platform is a tool to augment legal work — it does not provide legal advice.",
      ],
    },
    {
      id: "accounts",
      title: "3. Accounts and access",
      paragraphs: [
        "Firm administrators provision user accounts and assign roles. You are responsible for safeguarding credentials and for all activity under your account. Notify your administrator immediately if you suspect unauthorized access.",
      ],
      list: [
        "Role-based access control (RBAC) determines feature visibility",
        "Matter walls restrict case data to authorized participants",
        "Shared credentials are prohibited",
      ],
    },
    {
      id: "acceptable-use",
      title: "4. Acceptable use",
      paragraphs: ["You agree not to:"],
      list: [
        "Upload malware, unlawful content, or data you lack rights to process",
        "Attempt to bypass matter walls, audit logging, or security controls",
        "Reverse engineer, scrape, or overload the platform without written consent",
        "Use AI outputs as final legal advice without attorney review",
        "Misrepresent AI-generated content as human-authored where disclosure is required",
      ],
    },
    {
      id: "ai-disclaimer",
      title: "5. AI and professional responsibility",
      paragraphs: [
        "AI-generated summaries, research drafts, and contract analyses are advisory outputs requiring attorney review. LexFlow AI does not auto-file documents with courts, auto-send client communications, or replace professional judgment.",
        "Firms and individual users remain solely responsible for compliance with rules of professional conduct, court rules, and client engagement terms.",
      ],
    },
    {
      id: "ip",
      title: "6. Intellectual property",
      paragraphs: [
        "LexFlow AI retains all rights in the platform, documentation, and branding. Firms retain ownership of their case data, documents, and work product. Limited license grants for platform use are defined in the MSA.",
      ],
    },
    {
      id: "confidentiality",
      title: "7. Confidentiality",
      paragraphs: [
        "We treat Firm data as confidential per the DPA. Firm users must maintain client confidentiality consistent with applicable ethical obligations and Firm policies.",
      ],
    },
    {
      id: "availability",
      title: "8. Availability and support",
      paragraphs: [
        "We target 99.9% platform availability for production deployments. Scheduled maintenance is announced in advance. Support tiers and response times are defined in the MSA.",
      ],
    },
    {
      id: "limitation",
      title: "9. Limitation of liability",
      paragraphs: [
        "TO THE MAXIMUM EXTENT PERMITTED BY LAW, LEXFLOW AI SHALL NOT BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR FOR LOSS OF PROFITS, DATA, OR GOODWILL.",
        "Aggregate liability for direct damages is limited to fees paid in the twelve (12) months preceding the claim, except where prohibited by law.",
      ],
    },
    {
      id: "indemnification",
      title: "10. Indemnification",
      paragraphs: [
        "Firms agree to indemnify LexFlow AI against claims arising from Firm data, misuse of the platform, or violation of these Terms, except where caused by our gross negligence or willful misconduct.",
      ],
    },
    {
      id: "termination",
      title: "11. Termination",
      paragraphs: [
        "Either party may terminate per the MSA. We may suspend access immediately for security incidents or material breach. Upon termination, data export and deletion follow the DPA.",
      ],
    },
    {
      id: "governing-law",
      title: "12. Governing law",
      paragraphs: [
        "These Terms are governed by the laws of the State of Georgia, United States, without regard to conflict-of-law principles. Disputes shall be resolved in the courts of Fulton County, Georgia, unless the MSA specifies arbitration.",
      ],
    },
    {
      id: "contact",
      title: "13. Contact",
      paragraphs: [
        `Legal inquiries: ${siteConfig.supportEmail}`,
        `${siteConfig.legalName}, ${siteConfig.address.street}, ${siteConfig.address.city}, ${siteConfig.address.region} ${siteConfig.address.postalCode}`,
      ],
    },
  ],
};

export const legalPages = [aboutPage, privacyPage, termsPage] as const;
