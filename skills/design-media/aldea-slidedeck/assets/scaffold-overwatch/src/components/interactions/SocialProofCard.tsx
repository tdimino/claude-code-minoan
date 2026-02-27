/* ---------- Types ---------- */

interface Author {
  name: string;
  handle?: string;
  avatar?: string;
  verified?: boolean;
}

interface Metrics {
  replies?: string | number;
  retweets?: string | number;
  likes?: string | number;
  views?: string | number;
  reactions?: string | number;
}

interface ContentLine {
  text: string;
  bold?: boolean;
  highlight?: boolean;
}

interface SocialProofCardProps {
  variant: "twitter" | "linkedin" | "testimonial";
  author: Author;
  content: string | ContentLine[];
  metrics?: Metrics;
  timestamp?: string;
  className?: string;
}

/* ---------- Platform icons ---------- */

function XLogo({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function LinkedInLogo({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}

function VerifiedBadge() {
  return (
    <svg width={18} height={18} viewBox="0 0 22 22" fill="none">
      <path
        d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.855-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.69-.13.635-.08 1.293.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.604-.274 1.262-.144 1.897.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681.132-.637.075-1.299-.165-1.903.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"
        fill="#1D9BF0"
      />
    </svg>
  );
}

/* ---------- Metric icons ---------- */

const metricPaths: Record<string, string> = {
  reply:
    "M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 0 2.25-.893 4.306-2.394 5.862l-3.609 3.612c-.294.295-.767.295-1.061 0l-3.609-3.612c-1.5-1.556-2.394-3.613-2.394-5.862 0-.183.015-.364.03-.544H7.72C4.476 10 1.751 7.27 1.751 4z",
  repost:
    "M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2h6V20H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z",
  like: "M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-1.243.07-2.349.78-2.91 1.91-.552 1.12-.633 2.78.479 4.82 1.074 1.97 3.257 4.27 7.129 6.61 3.87-2.34 6.052-4.64 7.126-6.61 1.111-2.04 1.03-3.7.477-4.82-.56-1.13-1.666-1.84-2.908-1.91z",
  views:
    "M8.75 21V3h2v18h-2zM18.75 21V8.5h2V21h-2zM13.75 21v-9h2v9h-2zM3.75 21v-4h2v4h-2z",
};

function MetricIcon({ type }: { type: string }) {
  const d = metricPaths[type];
  if (!d) return null;
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="currentColor" style={{ opacity: 0.6 }}>
      <path d={d} />
    </svg>
  );
}

/* ---------- Main component ---------- */

export function SocialProofCard({ variant, author, content, metrics, timestamp, className }: SocialProofCardProps) {
  const lines: ContentLine[] =
    typeof content === "string" ? [{ text: content }] : content;

  const initial = author.name?.[0] ?? "?";

  function AvatarFallback() {
    return (
      <div
        className="w-12 h-12 rounded-full shrink-0 flex items-center justify-center"
        style={{ backgroundColor: "var(--color-border-light)" }}
      >
        <span className="text-[18px] font-bold" style={{ color: "var(--color-text-muted)" }}>
          {initial}
        </span>
      </div>
    );
  }

  return (
    <div
      className={className}
      style={{
        backgroundColor: "var(--color-bg-primary)",
        borderRadius: "16px",
        padding: "28px 32px",
        boxShadow: "0 4px 24px rgba(0, 0, 0, 0.3)",
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-center gap-3">
          {author.avatar ? (
            <img
              src={author.avatar}
              alt={author.name}
              className="w-12 h-12 rounded-full shrink-0"
              style={{ border: "1px solid var(--color-border-light)" }}
              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
            />
          ) : (
            <AvatarFallback />
          )}
          <div>
            <div className="flex items-center gap-1">
              <span
                className="text-[18px] font-bold"
                style={{ fontFamily: "var(--font-body)", color: "var(--color-text-primary)" }}
              >
                {author.name}
              </span>
              {author.verified && <VerifiedBadge />}
            </div>
            {author.handle && (
              <span
                className="text-[15px]"
                style={{ fontFamily: "var(--font-body)", color: "var(--color-text-muted)" }}
              >
                {author.handle}
              </span>
            )}
          </div>
        </div>
        <div style={{ color: "var(--color-text-primary)" }}>
          {variant === "twitter" && <XLogo size={22} />}
          {variant === "linkedin" && <LinkedInLogo size={22} />}
        </div>
      </div>

      {/* Content */}
      <div className="space-y-2" style={{ fontFamily: "var(--font-body)" }}>
        {lines.map((line, i) => (
          <p
            key={i}
            className="text-[20px] leading-[1.5]"
            style={{
              color: line.highlight ? "var(--color-orange)" : "var(--color-text-primary)",
              fontWeight: line.bold ? 600 : 400,
              opacity: !line.bold && !line.highlight ? 0.45 : 1,
            }}
          >
            {line.text}
          </p>
        ))}
      </div>

      {/* Timestamp */}
      {timestamp && (
        <div
          className="mt-4 text-[15px]"
          style={{ fontFamily: "var(--font-body)", color: "var(--color-text-muted)" }}
        >
          {timestamp}
        </div>
      )}

      {/* Metrics */}
      {metrics && variant === "twitter" && (
        <div
          className="mt-3 flex items-center justify-between"
          style={{ color: "var(--color-text-muted)" }}
        >
          {[
            { type: "reply", count: metrics.replies },
            { type: "repost", count: metrics.retweets },
            { type: "like", count: metrics.likes },
            { type: "views", count: metrics.views },
          ]
            .filter((m) => m.count != null)
            .map((m) => (
              <div key={m.type} className="flex items-center gap-1.5">
                <MetricIcon type={m.type} />
                <span
                  className="text-[15px]"
                  style={{ fontFamily: "var(--font-body)", color: "var(--color-text-muted)" }}
                >
                  {m.count}
                </span>
              </div>
            ))}
        </div>
      )}

      {/* LinkedIn reactions */}
      {metrics && variant === "linkedin" && metrics.reactions && (
        <div
          className="mt-3 flex items-center gap-2 text-[14px]"
          style={{ fontFamily: "var(--font-body)", color: "var(--color-text-muted)" }}
        >
          <span>{metrics.reactions} reactions</span>
        </div>
      )}
    </div>
  );
}
