// footer: brutalist credit row with tagged links.
function MailIcon() {
  return (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="1" /><path d="m22 7-10 6L2 7" /></svg>);
}

export function Footer() {
  const links = [
    { href: "mailto:ashrafsameer682@gmail.com", label: "ashrafsameer682@gmail.com", icon: <MailIcon /> },
  ];
  return (
    <footer className="mt-24 border-t-2 border-white/15 pt-8">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="font-mono text-sm uppercase tracking-wide text-white/45">
          Built by <span className="text-white/85">Syed Sameer Rizvi</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              target={l.href.startsWith("http") ? "_blank" : undefined}
              rel={l.href.startsWith("http") ? "noopener noreferrer" : undefined}
              className="flex items-center gap-2 border-2 border-white/20 px-3 py-1.5 font-mono text-xs text-white/55 transition-colors hover:border-white/40 hover:text-white/90"
            >
              {l.icon}
              <span>{l.label}</span>
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}

