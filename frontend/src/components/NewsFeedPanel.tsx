import type { NewsItem } from "../types";


interface NewsFeedPanelProps {
  items: NewsItem[];
}


function toneClass(label: string) {
  return `tone-${label}`;
}


export function NewsFeedPanel({ items }: NewsFeedPanelProps) {
  return (
    <section className="glass-card news-card">
      <div className="panel-header">
        <div>
          <div className="section-kicker">News Feed</div>
          <h2>Headline sentiment tape</h2>
        </div>
        <p>Recent articles scored with FinBERT and color-coded by tone.</p>
      </div>

      <div className="news-list">
        {items.length === 0 ? (
          <div className="empty-state">No matching articles found for this ticker yet.</div>
        ) : (
          items.map((item) => (
            <a
              key={`${item.url}-${item.published_at}`}
              className={`news-item ${toneClass(item.sentiment.label)}`}
              href={item.url || "#"}
              target="_blank"
              rel="noreferrer"
            >
              <div className="news-meta">
                <span>{item.source || "Unknown source"}</span>
                <span>{item.published_at || "Pending timestamp"}</span>
              </div>
              <strong>{item.headline}</strong>
              <div className="news-score">
                <span>{item.sentiment.label}</span>
                <span>{item.sentiment.score.toFixed(3)}</span>
              </div>
            </a>
          ))
        )}
      </div>
    </section>
  );
}
