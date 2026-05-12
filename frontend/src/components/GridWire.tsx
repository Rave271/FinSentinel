export function GridWire({ title = "Gridwire backdrop" }: { title?: string }) {
  return (
    <svg className="gridwire" viewBox="0 0 900 700" role="img" aria-label={title}>
      <defs>
        <radialGradient id="fs-grid-glow" cx="50%" cy="35%" r="70%">
          <stop offset="0%" stopColor="rgba(180, 255, 72, 0.22)" />
          <stop offset="55%" stopColor="rgba(180, 255, 72, 0.06)" />
          <stop offset="100%" stopColor="rgba(180, 255, 72, 0)" />
        </radialGradient>
        <linearGradient id="fs-grid-stroke" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="rgba(180, 255, 72, 0)" />
          <stop offset="45%" stopColor="rgba(180, 255, 72, 0.46)" />
          <stop offset="100%" stopColor="rgba(180, 255, 72, 0)" />
        </linearGradient>
        <filter id="fs-grid-blur" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="0.8" />
        </filter>
      </defs>

      <rect x="0" y="0" width="900" height="700" fill="url(#fs-grid-glow)" />

      {/* perspective grid */}
      <g fill="none" stroke="url(#fs-grid-stroke)" strokeWidth="1.2" opacity="0.95" filter="url(#fs-grid-blur)">
        {/* vertical perspective lines */}
        {Array.from({ length: 22 }).map((_, idx) => {
          const t = idx / 21;
          const xTop = 260 + t * 380;
          const xBottom = 80 + t * 740;
          return <path key={`v-${idx}`} d={`M${xTop} 210 L${xBottom} 670`} />;
        })}
        {/* horizontal perspective lines */}
        {Array.from({ length: 18 }).map((_, idx) => {
          const t = idx / 17;
          const y = 240 + t * 420;
          const inset = 110 * (1 - t);
          return <path key={`h-${idx}`} d={`M${160 + inset} ${y} L${740 - inset} ${y}`} opacity={0.86} />;
        })}
      </g>

      {/* orbit + nodes */}
      <g fill="none" stroke="rgba(180, 255, 72, 0.28)" strokeWidth="1">
        <circle cx="450" cy="280" r="120" />
        <circle cx="450" cy="280" r="188" opacity="0.65" />
      </g>
      <g fill="rgba(180, 255, 72, 0.75)">
        <circle cx="580" cy="280" r="3.2" />
        <circle cx="360" cy="220" r="2.6" opacity="0.8" />
        <circle cx="420" cy="430" r="2.8" opacity="0.8" />
      </g>
    </svg>
  );
}

