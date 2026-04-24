// app/[locale]/academy/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

interface AcademyResource {
  id:            string;
  certification: string;
  level:         string;
  title:         string;
  description:   string;
  resource_url:  string;
  status:        string;
  tags:          string[];
  is_free:       boolean;
}

const CERTS  = ["VCP", "CCNA", "CCNP", "CCIE", "CISSP", "CEH", "AWS_SA"];
const LEVELS = ["beginner", "associate", "professional", "expert"];

const LEVEL_COLORS: Record<string, string> = {
  beginner:     "bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300",
  associate:    "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  professional: "bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  expert:       "bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300",
};

const CERT_ICONS: Record<string, string> = {
  VCP:    "🔵",
  CCNA:   "🌐",
  CCNP:   "🌐",
  CCIE:   "🌐",
  CISSP:  "🔒",
  CEH:    "⚔️",
  AWS_SA: "☁️",
};

export default function AcademyPage() {
  const t = useTranslations("academy");

  const [resources, setResources]   = useState<AcademyResource[]>([]);
  const [loading, setLoading]       = useState(true);
  const [certFilter, setCertFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [freeOnly, setFreeOnly]     = useState(false);

  useEffect(() => {
    fetchResources();
  }, [certFilter, levelFilter, freeOnly]);

  async function fetchResources() {
    setLoading(true);
    const params = new URLSearchParams({ limit: "50" });
    if (certFilter)  params.set("certification", certFilter);
    if (levelFilter) params.set("level", levelFilter);
    if (freeOnly)    params.set("is_free", "true");

    const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/academy?${params}`);
    const data = await res.json();
    setResources(data);
    setLoading(false);
  }

  // Group by certification
  const grouped = resources.reduce<Record<string, AcademyResource[]>>((acc, r) => {
    if (!acc[r.certification]) acc[r.certification] = [];
    acc[r.certification].push(r);
    return acc;
  }, {});

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          {t("title")}
        </h1>
        <p className="text-gray-600 dark:text-gray-400">{t("subtitle")}</p>
      </header>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-8 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
        <select
          value={certFilter}
          onChange={(e) => setCertFilter(e.target.value)}
          className="text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800"
        >
          <option value="">{t("filterCert")}: All</option>
          {CERTS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800"
        >
          <option value="">{t("allLevels")}</option>
          {LEVELS.map((l) => (
            <option key={l} value={l}>{t(l as "beginner" | "associate" | "professional" | "expert")}</option>
          ))}
        </select>

        <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={freeOnly}
            onChange={(e) => setFreeOnly(e.target.checked)}
            className="rounded"
          />
          {t("free")} only
        </label>
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-10">
          {Object.entries(grouped).map(([cert, items]) => (
            <section key={cert}>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 pb-2 border-b border-gray-200 dark:border-gray-700">
                <span>{CERT_ICONS[cert] ?? "📚"}</span>
                {cert}
                <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                  ({items.length} resources)
                </span>
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {items.map((r) => (
                  <a
                    key={r.id}
                    href={r.resource_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all bg-white dark:bg-gray-800 group"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="font-medium text-gray-900 dark:text-gray-100 text-sm group-hover:text-blue-600 dark:group-hover:text-blue-400 leading-snug">
                        {r.title}
                      </h3>
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${LEVEL_COLORS[r.level]}`}>
                          {r.level}
                        </span>
                        {r.is_free ? (
                          <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                            {t("free")}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">{t("paid")}</span>
                        )}
                      </div>
                    </div>

                    <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-2">
                      {r.description}
                    </p>

                    <div className="flex flex-wrap gap-1">
                      {r.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </a>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </main>
  );
}
