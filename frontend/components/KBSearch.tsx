// components/KBSearch.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { apiFetch, ApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

// ─── Types ───────────────────────────────────────────────────
interface KBArticle {
  id: string;
  manufacturer_id: string;
  manufacturer_name: string;
  title: string;
  description: string;
  source_url: string;
  tags: string[];
  status: "online" | "broken" | "unchecked";
  resolution_score: number | null;
  total_votes: number | null;
  created_at: string;
}

interface Manufacturer {
  id: string;
  slug: string;
  display_name: string;
}

interface VoteResponse {
  kb_id: string;
  vote: "like" | "dislike" | null;
  resolution_score: number | null;
  total_votes: number;
}

interface SearchFilters {
  manufacturer?: string;
  status?: "online" | "broken";
  tags?: string;
}

// ─── JSON-LD inline (App Router way) ──────────────────────────
function FaqJsonLd({ articles }: { articles: KBArticle[] }) {
  if (articles.length === 0) return null;
  const schema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: articles.slice(0, 20).map((a) => ({
      "@type": "Question",
      name: a.title,
      acceptedAnswer: {
        "@type": "Answer",
        text: a.description,
        url: a.source_url,
      },
    })),
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

// ─── UI atoms ─────────────────────────────────────────────────
function ResolutionBadge({ score }: { score: number | null }) {
  if (score === null) return null;
  const color =
    score >= 75 ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300" :
    score >= 50 ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300" :
                  "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {score}%
    </span>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    online:    "bg-green-400",
    broken:    "bg-red-400",
    unchecked: "bg-gray-400",
  };
  return (
    <span
      title={status}
      className={`inline-block w-2 h-2 rounded-full ${colors[status] ?? "bg-gray-400"}`}
    />
  );
}

// ─── Article Card ─────────────────────────────────────────────
function ArticleCard({
  article,
  onVote,
  userVote,
  voting,
}: {
  article: KBArticle;
  onVote: (id: string, vote: "like" | "dislike") => void;
  userVote: "like" | "dislike" | null;
  voting: boolean;
}) {
  const t = useTranslations("kb");

  return (
    <article className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow bg-white dark:bg-gray-800 flex flex-col">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <StatusDot status={article.status} />
            <span className="text-xs text-gray-500 dark:text-gray-400 truncate font-mono">
              {article.manufacturer_name}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm leading-snug mb-1">
            <a
              href={article.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600 dark:hover:text-blue-400"
            >
              {article.title}
            </a>
          </h3>
          <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
            {article.description}
          </p>
          <div className="flex flex-wrap gap-1 mb-2">
            {article.tags.slice(0, 5).map((tag) => (
              <span
                key={tag}
                className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded font-mono"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
        <ResolutionBadge score={article.resolution_score} />
      </div>

      <div className="flex items-center gap-2 pt-2 mt-auto border-t border-gray-100 dark:border-gray-700">
        <span className="text-xs text-gray-500 dark:text-gray-400 mr-auto font-mono">
          {article.total_votes ?? 0} {t("votes")}
        </span>
        <button
          onClick={() => onVote(article.id, "like")}
          disabled={voting}
          aria-label={t("like")}
          className={`px-2.5 py-1 rounded text-xs flex items-center gap-1 transition-colors disabled:opacity-50 ${
            userVote === "like"
              ? "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300"
              : "text-gray-500 hover:bg-green-50 dark:hover:bg-green-900/20"
          }`}
        >
          👍 {t("like")}
        </button>
        <button
          onClick={() => onVote(article.id, "dislike")}
          disabled={voting}
          aria-label={t("dislike")}
          className={`px-2.5 py-1 rounded text-xs flex items-center gap-1 transition-colors disabled:opacity-50 ${
            userVote === "dislike"
              ? "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300"
              : "text-gray-500 hover:bg-red-50 dark:hover:bg-red-900/20"
          }`}
        >
          👎 {t("dislike")}
        </button>
      </div>
    </article>
  );
}

// ─── Main component ──────────────────────────────────────────
export default function KBSearch() {
  const t = useTranslations("kb");
  const { user, login } = useAuth();

  const [query, setQuery]                 = useState("");
  const [articles, setArticles]           = useState<KBArticle[]>([]);
  const [manufacturers, setManufacturers] = useState<Manufacturer[]>([]);
  const [loading, setLoading]             = useState(false);
  const [filters, setFilters]             = useState<SearchFilters>({});
  const [userVotes, setUserVotes]         = useState<Record<string, "like" | "dislike">>({});
  const [votingIds, setVotingIds]         = useState<Set<string>>(new Set());

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cargar manufacturers una vez
  useEffect(() => {
    apiFetch<Manufacturer[]>("/api/manufacturers")
      .then(setManufacturers)
      .catch((err) => {
        console.error("Failed to load manufacturers:", err);
        setManufacturers([]);
      });
  }, []);

  // Búsqueda debounced
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(fetchArticles, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, filters]);

  async function fetchArticles() {
    setLoading(true);
    try {
      const params = new URLSearchParams({ q: query, limit: "20" });
      if (filters.manufacturer) params.set("manufacturer", filters.manufacturer);
      if (filters.status)       params.set("status", filters.status);
      if (filters.tags)         params.set("tags", filters.tags);

      const data = await apiFetch<KBArticle[]>(`/api/kb/search?${params}`);
      setArticles(data);
    } catch (err) {
      console.error("Search failed:", err);
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleVote(kbId: string, vote: "like" | "dislike") {
    if (!user) {
      login();
      return;
    }

    const currentVote = userVotes[kbId] ?? null;
    setVotingIds((s) => new Set(s).add(kbId));

    try {
      let result: VoteResponse;

      if (currentVote === vote) {
        // Toggle off: retirar voto
        result = await apiFetch<VoteResponse>(`/api/kb/vote/${kbId}`, {
          method: "DELETE",
        });
        setUserVotes((prev) => {
          const next = { ...prev };
          delete next[kbId];
          return next;
        });
      } else {
        // Insertar / cambiar voto
        result = await apiFetch<VoteResponse>("/api/kb/vote", {
          method: "POST",
          body: JSON.stringify({ kb_id: kbId, vote }),
        });
        setUserVotes((prev) => ({ ...prev, [kbId]: vote }));
      }

      // Actualizar resolution score localmente
      setArticles((prev) =>
        prev.map((a) =>
          a.id === kbId
            ? {
                ...a,
                resolution_score: result.resolution_score,
                total_votes: result.total_votes,
              }
            : a,
        ),
      );
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        login();
      } else {
        console.error("Vote failed:", err);
      }
    } finally {
      setVotingIds((s) => {
        const next = new Set(s);
        next.delete(kbId);
        return next;
      });
    }
  }

  return (
    <>
      <FaqJsonLd articles={articles} />

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Search */}
        <div className="relative mb-4">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("searchPlaceholder")}
            aria-label={t("searchLabel")}
            className="w-full px-4 py-3 pl-11 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <svg
            className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2 mb-6">
          <select
            value={filters.manufacturer ?? ""}
            onChange={(e) =>
              setFilters((f) => ({ ...f, manufacturer: e.target.value || undefined }))
            }
            className="text-xs border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-mono"
          >
            <option value="">{t("allManufacturers")}</option>
            {manufacturers.map((m) => (
              <option key={m.slug} value={m.slug}>
                {m.display_name}
              </option>
            ))}
          </select>

          <select
            value={filters.status ?? ""}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                status: (e.target.value as "online" | "broken") || undefined,
              }))
            }
            className="text-xs border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-mono"
          >
            <option value="">{t("allStatuses")}</option>
            <option value="online">{t("online")}</option>
            <option value="broken">{t("broken")}</option>
          </select>
        </div>

        {/* Results */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-36 bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse"
              />
            ))}
          </div>
        ) : articles.length === 0 && query ? (
          <p className="text-center text-gray-500 dark:text-gray-400 py-12">
            {t("noResults")}
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {articles.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                onVote={handleVote}
                userVote={userVotes[article.id] ?? null}
                voting={votingIds.has(article.id)}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
