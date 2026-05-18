export function Insignia({ title = "FinSentinel" }: { title?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      width="44"
      height="44"
      role="img"
      aria-label={title}
      className="insignia"
    >
      <defs>
        <linearGradient id="fs-badge" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="color-mix(in srgb, var(--accent-neon) 55%, transparent)" />
          <stop offset="0.5" stopColor="rgba(255, 255, 255, 0.08)" />
          <stop offset="1" stopColor="color-mix(in srgb, var(--accent-crimson) 38%, transparent)" />
        </linearGradient>
        <radialGradient id="fs-glass" cx="28%" cy="24%" r="80%">
          <stop offset="0" stopColor="rgba(255, 255, 255, 0.22)" />
          <stop offset="0.5" stopColor="rgba(255, 255, 255, 0.06)" />
          <stop offset="1" stopColor="rgba(255, 255, 255, 0)" />
        </radialGradient>
      </defs>

      {/* badge */}
      <circle cx="32" cy="32" r="26" fill="url(#fs-badge)" opacity="0.34" />
      <circle cx="32" cy="32" r="26" fill="url(#fs-glass)" opacity="0.9" />
      <circle
        cx="32"
        cy="32"
        r="26"
        fill="none"
        stroke="color-mix(in srgb, var(--text-main) 32%, transparent)"
        strokeWidth="1.2"
      />

      {/* subtle grid */}
      <g opacity="0.65" stroke="color-mix(in srgb, var(--text-main) 16%, transparent)" strokeWidth="1">
        <path d="M18 24h28" strokeLinecap="round" />
        <path d="M18 32h28" strokeLinecap="round" />
        <path d="M18 40h28" strokeLinecap="round" />
        <path d="M24 18v28" strokeLinecap="round" />
        <path d="M32 18v28" strokeLinecap="round" />
        <path d="M40 18v28" strokeLinecap="round" />
      </g>

      {/* price path */}
      <path
        d="M18 40c5-7 8-6 12-12s8-4 12-8 6-5 10-2"
        fill="none"
        stroke="color-mix(in srgb, var(--accent-neon) 70%, var(--text-main))"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* nodes */}
      <g fill="color-mix(in srgb, var(--accent-neon) 75%, var(--text-main))">
        <circle cx="18" cy="40" r="1.6" />
        <circle cx="30" cy="28" r="1.6" />
        <circle cx="42" cy="20" r="1.6" />
        <circle cx="52" cy="18" r="1.6" />
      </g>

      {/* sentinel eye */}
      <path
        d="M18 22c3.5-3 8.5-3 12 0-3.5 3-8.5 3-12 0Z"
        fill="color-mix(in srgb, var(--accent-crimson) 18%, transparent)"
        stroke="color-mix(in srgb, var(--accent-crimson) 48%, transparent)"
        strokeWidth="1"
      />
      <circle cx="24" cy="22" r="1.4" fill="color-mix(in srgb, var(--accent-crimson) 70%, var(--text-main))" />
    </svg>
  );
}
