// Deterministic pseudo-random jitter for institutions without geocoded
// coordinates, so their marker position is stable across renders (same
// institution always lands in the same spot) without needing real
// coordinates. Not the same PRNG as the Python dashboard's numpy
// default_rng, just a same-purpose deterministic substitute keyed the
// same way (country + index).
function hashSeed(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function mulberry32(seed: number) {
  let a = seed;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function jitteredPoint(
  key: string,
  centerLat: number,
  centerLon: number,
  jitterDeg = 0.55,
): { latitude: number; longitude: number } {
  const rand = mulberry32(hashSeed(key));
  const latOffset = (rand() * 2 - 1) * jitterDeg;
  const lonOffset = (rand() * 2 - 1) * jitterDeg;
  return { latitude: centerLat + latOffset, longitude: centerLon + lonOffset };
}
