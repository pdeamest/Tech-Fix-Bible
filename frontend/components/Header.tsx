// components/Header.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

const LOCALES = ["en", "es"] as const;

export default function Header() {
  const locale = useLocale();
  const pathname = usePathname();
  const t = useTranslations("nav");
  const { user, loading, login, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Cerrar dropdown al clickear fuera
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [menuOpen]);

  // Mantiene la ruta actual al cambiar de locale
  function switchLocaleHref(target: string): string {
    // pathname incluye el locale actual, ej: /en/academy → /es/academy
    const segments = (pathname ?? `/${locale}`).split("/");
    segments[1] = target;
    return segments.join("/") || `/${target}`;
  }

  return (
    <header className="sticky top-0 z-40 bg-white/95 dark:bg-gray-900/95 backdrop-blur border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">
        <Link href={`/${locale}`} className="flex items-center gap-2 shrink-0">
          <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white font-mono text-xs font-bold">
            KB
          </div>
          <span className="font-mono font-bold text-gray-900 dark:text-gray-100 tracking-tight hidden sm:inline">
            TechKB
          </span>
        </Link>

        <nav className="flex-1 flex items-center gap-1 text-sm">
          <Link
            href={`/${locale}`}
            className="px-3 py-1.5 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {t("search")}
          </Link>
          <Link
            href={`/${locale}/academy`}
            className="px-3 py-1.5 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {t("academy")}
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          {/* Lang switcher */}
          <div className="flex items-center rounded-md border border-gray-200 dark:border-gray-700 overflow-hidden text-xs font-mono">
            {LOCALES.map((l) => (
              <Link
                key={l}
                href={switchLocaleHref(l)}
                className={`px-2 py-1 transition-colors ${
                  l === locale
                    ? "bg-blue-600 text-white"
                    : "text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                {l.toUpperCase()}
              </Link>
            ))}
          </div>

          {/* Auth */}
          {loading ? (
            <div className="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 animate-pulse" />
          ) : user ? (
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"
              >
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-semibold">
                  {user.display_name[0]?.toUpperCase() ?? "?"}
                </div>
                <span className="hidden sm:inline">{user.display_name}</span>
                <span className="text-xs text-gray-400 font-mono">
                  ★{user.karma_score}
                </span>
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-2 w-52 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1">
                  <div className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700 truncate">
                    {user.email}
                  </div>
                  <button
                    onClick={() => {
                      void logout();
                      setMenuOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    {t("logout")}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={login}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded"
            >
              {t("login")}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
