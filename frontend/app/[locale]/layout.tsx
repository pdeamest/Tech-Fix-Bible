// app/[locale]/layout.tsx
// Layout del locale: conecta i18n (next-intl) + AuthProvider + Header global.

import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, unstable_setRequestLocale } from "next-intl/server";
import { AuthProvider } from "@/contexts/AuthContext";
import Header from "@/components/Header";

const LOCALES = ["en", "es"] as const;

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: { locale: string };
}) {
  const { locale } = params;

  if (!LOCALES.includes(locale as (typeof LOCALES)[number])) {
    notFound();
  }

  // Enable static rendering for this locale
  unstable_setRequestLocale(locale);

  const messages = await getMessages();

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <AuthProvider>
        <Header />
        <div className="min-h-[calc(100vh-56px)] bg-gray-50 dark:bg-gray-950">
          {children}
        </div>
      </AuthProvider>
    </NextIntlClientProvider>
  );
}
