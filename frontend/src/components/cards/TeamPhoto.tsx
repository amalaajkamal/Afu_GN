import { User } from "lucide-react";

function LinkedinIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.34V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.38-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.07 2.07 0 1 1 0-4.13 2.07 2.07 0 0 1 0 4.13ZM7.12 20.45H3.56V9h3.56v11.45Z" />
    </svg>
  );
}

export function TeamPhoto({
  src,
  name,
  role,
  linkedin,
}: {
  /** Drop a file at frontend/public/team/<file>.jpg and pass "/team/<file>.jpg" here. */
  src?: string;
  name: string;
  role: string;
  linkedin?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3 text-center">
      <div className="flex h-32 w-32 shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-border bg-surface-muted shadow-sm sm:h-36 sm:w-36">
        {src ? (
          <img src={src} alt={name} className="h-full w-full object-cover grayscale" />
        ) : (
          <User size={44} strokeWidth={1.5} className="text-text-secondary/50" />
        )}
      </div>
      <div>
        <p className="font-semibold text-text-primary">{name}</p>
        <p className="text-sm text-text-secondary">{role}</p>
        {linkedin && (
          <a
            href={linkedin}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`${name} on LinkedIn`}
            className="mt-1 inline-flex items-center justify-center text-text-secondary transition-colors hover:text-ink-terracotta"
          >
            <LinkedinIcon />
          </a>
        )}
      </div>
    </div>
  );
}
