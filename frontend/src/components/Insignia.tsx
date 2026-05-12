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
        <linearGradient id="fs-insignia" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="rgba(255,255,255,0.72)" />
          <stop offset="0.45" stopColor="rgba(255,255,255,0.18)" />
          <stop offset="1" stopColor="rgba(255,255,255,0.0)" />
        </linearGradient>
      </defs>

      <path
        d="M32 4c10 0 22 6 22 6v18c0 18-13 30-22 32C23 58 10 46 10 28V10s12-6 22-6Z"
        fill="rgba(172, 35, 44, 0.18)"
        stroke="rgba(255,255,255,0.38)"
        strokeWidth="1.2"
      />
      <path
        d="M32 10c7.4 0 16 4 16 4v13.5c0 13.5-9.1 22.3-16 24-6.9-1.7-16-10.5-16-24V14s8.6-4 16-4Z"
        fill="url(#fs-insignia)"
        opacity="0.55"
      />

      <path
        d="M21 24h22M21 32h22M21 40h22"
        stroke="rgba(23, 19, 17, 0.62)"
        strokeWidth="1.4"
        strokeLinecap="round"
        opacity="0.7"
      />

      <path
        d="M24 22c0-6 5-10 8-10s8 4 8 10"
        stroke="rgba(23, 19, 17, 0.72)"
        strokeWidth="1.6"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M26 44c3 3.2 7.2 6 12 6s9-2.8 12-6"
        stroke="rgba(172, 35, 44, 0.72)"
        strokeWidth="1.8"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

