// Exact V3 underdamped solution: preserves value AND velocity across retargets.
export function springStep(value, velocity, target, seconds, damping = 30) {
  if (seconds <= 0) return [value, velocity];
  const half = damping / 2, frequency = Math.sqrt(500 - half * half);
  const displacement = value - target, coefficient = (velocity + half * displacement) / frequency;
  const decay = Math.exp(-half * seconds), c = Math.cos(frequency * seconds), s = Math.sin(frequency * seconds);
  const offset = displacement * c + coefficient * s;
  const rate = -displacement * frequency * s + coefficient * frequency * c;
  return [target + decay * offset, decay * (rate - half * offset)];
}
