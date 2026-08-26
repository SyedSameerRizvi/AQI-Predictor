// Pakistan air-quality news: title + source + date, links out to the article.
import { useEffect, useState } from "react";
import { motion } from "motion/react";
import type { NewsItem } from "@/lib/types";
import { fetchNews } from "@/lib/api";

interface NewsPanelProps {
  accent: string;
}

function ExtLinkIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 17 17 7M9 7h8v8" />
    </svg>
  );
}

export function NewsPanel({ accent }: NewsPanelProps) {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchNews()
      .then((n) => active && setItems(n))
      .catch(() => active && setItems([]))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  if (!loading && items.length === 0) return null;

  return (
    <div className="border-2 border-white/15 bg-black p-6 shadow-hard">
      <h2 className="font-display text-lg font-extrabold uppercase text-white">
        Pakistan air quality news
      </h2>

      {loading ? (
        <div className="mt-4 font-mono text-xs uppercase tracking-wide text-white/35">
          Loading headlines...
        </div>
      ) : (
        <ul className="mt-4 divide-y divide-white/10">
          {items.map((n, i) => (
            <motion.li
              key={n.url}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35, delay: 0.06 * i }}
            >
              <a
                href={n.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-start justify-between gap-4 py-3 transition-colors hover:bg-white/[0.03]"
              >
                <div>
                  <div className="text-sm font-medium text-white/85 group-hover:text-white">
                    {n.title}
                  </div>
                  <div className="mt-1 font-mono text-[11px] uppercase tracking-wide text-white/40">
                    {n.source}
                    {n.published_at ? ` / ${new Date(n.published_at).toLocaleDateString()}` : ""}
                  </div>
                </div>
                <span
                  className="mt-1 shrink-0 opacity-40 transition-opacity group-hover:opacity-100"
                  style={{ color: accent }}
                >
                  <ExtLinkIcon />
                </span>
              </a>
            </motion.li>
          ))}
        </ul>
      )}
    </div>
  );
}

