import { useEffect, useState } from "react";

type Theme = "light" | "dark" | null;

const read = (): Theme => {
  try {
    const stored = localStorage.getItem("theme");
    return stored === "light" || stored === "dark" ? stored : null;
  } catch {
    return null;
  }
};

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(read);
  const systemDark = typeof matchMedia !== "undefined" && matchMedia("(prefers-color-scheme: dark)").matches;
  const effective = theme ?? (systemDark ? "dark" : "light");

  useEffect(() => {
    if (theme) document.documentElement.dataset.theme = theme;
    else delete document.documentElement.dataset.theme;
    try {
      if (theme) localStorage.setItem("theme", theme);
      else localStorage.removeItem("theme");
    } catch {
      // Storage can be unavailable in private windows; the toggle still works for this visit.
    }
  }, [theme]);

  const next = effective === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
    >
      {effective === "dark" ? (
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
          {Array.from({ length: 8 }, (_, i) => {
            const a = (i * Math.PI) / 4;
            return (
              <line
                key={i}
                x1={12 + Math.cos(a) * 7.5}
                y1={12 + Math.sin(a) * 7.5}
                x2={12 + Math.cos(a) * 10}
                y2={12 + Math.sin(a) * 10}
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            );
          })}
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10Z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  );
}
