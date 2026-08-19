import { useEffect, useState } from "react";

const DEFAULT_THRESHOLD_MS = 20_000;

// Flips true once `active` has stayed true continuously for `thresholdMs`,
// resets the moment it goes false. Used by the research pages to show an
// extra "this is taking longer than usual" note during the bootstrap
// loading state without claiming a hard failure -- the backend keeps
// retrying on its own TTL/polling schedule regardless.
export function useLongWait(active: boolean, thresholdMs = DEFAULT_THRESHOLD_MS): boolean {
  const [waitedLong, setWaitedLong] = useState(false);

  useEffect(() => {
    if (!active) {
      setWaitedLong(false);
      return;
    }
    const timer = setTimeout(() => setWaitedLong(true), thresholdMs);
    return () => clearTimeout(timer);
  }, [active, thresholdMs]);

  return waitedLong;
}
