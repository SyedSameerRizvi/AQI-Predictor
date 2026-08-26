// footer: brutalist credit row with tagged links.
function MailIcon() {
  return (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="1" /><path d="m22 7-10 6L2 7" /></svg>);
}
function LinkedInIcon() {
  return (<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.55V9h3.57v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z" /></svg>);
}
function GlobeIcon() {
  return (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>);
}

export function Footer() {
  const links = [
    { href: "mailto:ashrafsameer682@gmail.com", label: "ashrafsameer682@gmail.com", icon: <MailIcon /> },
    { href: "https://www.linkedin.com/in/syed-sameer-rizvi", label: "LinkedIn", icon: <LinkedInIcon /> },
    { href: "https://syedsameerrizvi.netlify.app", label: "Portfolio", icon: <GlobeIcon /> },
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

