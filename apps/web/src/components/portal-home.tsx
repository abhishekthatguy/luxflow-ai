"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth";
import { isPortalUser } from "@/lib/permissions";

type PortalHomeProps = {
  clientName?: string;
  clientEmail?: string;
};

export function PortalHome({ clientName, clientEmail }: PortalHomeProps) {
  const { user, loading } = useAuth();
  const greetingName = user?.firstName || clientName;
  const greeting = greetingName ? `Welcome, ${greetingName}` : "Welcome to your client portal";

  if (!loading && user && isPortalUser(user)) {
    return (
      <div className="space-y-8">
        <section className="rounded-2xl border border-emerald-100 bg-white p-8 shadow-sm">
          <p className="text-sm font-medium uppercase tracking-wide text-emerald-700">Signed in</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">{greeting}</h1>
          <p className="mt-4 max-w-2xl text-slate-600">
            You are signed in to the LexFlow client portal as{" "}
            <span className="font-medium text-slate-800">{user.email}</span>. Your firm will post
            intake updates, document requests, and case milestones here as your matter progresses.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="mailto:clawtbot@gmail.com"
              className="rounded-md bg-emerald-800 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-900"
            >
              Contact the firm
            </a>
            <Link
              href="/portal/login"
              className="rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Account
            </Link>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <article className="rounded-xl border border-slate-200 bg-white p-6">
            <p className="text-xs font-semibold uppercase text-emerald-700">Step 1</p>
            <h2 className="mt-2 font-semibold text-slate-900">Profile active</h2>
            <p className="mt-2 text-sm text-slate-600">Your client record is linked to this portal account.</p>
          </article>
          <article className="rounded-xl border border-slate-200 bg-white p-6">
            <p className="text-xs font-semibold uppercase text-emerald-400">Step 2</p>
            <h2 className="mt-2 font-semibold text-slate-900">Intake review</h2>
            <p className="mt-2 text-sm text-slate-600">The firm may reach out for documents or clarifications.</p>
          </article>
          <article className="rounded-xl border border-slate-200 bg-white p-6">
            <p className="text-xs font-semibold uppercase text-slate-400">Step 3</p>
            <h2 className="mt-2 font-semibold text-slate-900">Case milestones</h2>
            <p className="mt-2 text-sm text-slate-600">Timeline and document requests will appear here when ready.</p>
          </article>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-emerald-100 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-wide text-emerald-700">Client onboarding</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">{greeting}</h1>
        <p className="mt-4 max-w-2xl text-slate-600">
          Your profile has been created with our firm. Use this portal to track intake progress,
          upload documents when requested, and view case milestones as your matter moves forward.
        </p>
        {clientEmail && (
          <p className="mt-3 text-sm text-slate-500">
            Registered email: <span className="font-medium text-slate-700">{clientEmail}</span>
          </p>
        )}
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/portal/forgot-password"
            className="rounded-md bg-emerald-800 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-900"
          >
            Set or reset password
          </Link>
          <Link
            href="/portal/login"
            className="rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Sign in
          </Link>
          <a
            href="mailto:clawtbot@gmail.com"
            className="rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Contact the firm
          </a>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-slate-200 bg-white p-6">
          <p className="text-xs font-semibold uppercase text-emerald-700">Step 1</p>
          <h2 className="mt-2 font-semibold text-slate-900">Profile created</h2>
          <p className="mt-2 text-sm text-slate-600">
            Your client record is active. Our intake team has been notified.
          </p>
        </article>
        <article className="rounded-xl border border-slate-200 bg-white p-6">
          <p className="text-xs font-semibold uppercase text-slate-400">Step 2</p>
          <h2 className="mt-2 font-semibold text-slate-900">Intake review</h2>
          <p className="mt-2 text-sm text-slate-600">
            A team member will reach out to confirm details and gather initial documents.
          </p>
        </article>
        <article className="rounded-xl border border-slate-200 bg-white p-6">
          <p className="text-xs font-semibold uppercase text-slate-400">Step 3</p>
          <h2 className="mt-2 font-semibold text-slate-900">Case opened</h2>
          <p className="mt-2 text-sm text-slate-600">
            Once intake is complete, you will see your matter timeline and document requests here.
          </p>
        </article>
      </section>

      <section className="rounded-xl border border-amber-100 bg-amber-50/80 p-6 text-sm text-amber-950">
        <p className="font-medium">Attorney–client privilege</p>
        <p className="mt-2 text-amber-900/90">
          Information shared through this portal is handled under your firm&apos;s confidentiality
          policies. Do not forward portal links to unauthorized third parties.
        </p>
      </section>
    </div>
  );
}
