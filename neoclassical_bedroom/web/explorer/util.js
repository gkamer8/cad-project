// Shared helpers: units, room coordinates, DOM and easing.
export const IN = 0.0254; // metres per inch (the model is authored in inches, exported in metres)
export const ROOM = { L: 192 * IN, W: 144 * IN, H: 96 * IN };

const EIGHTHS = ['', ' 1/8', ' 1/4', ' 3/8', ' 1/2', ' 5/8', ' 3/4', ' 7/8'];

/** Architectural length: 16'-0", 2'-8", 7 1/4". */
export function ftIn(inches) {
  const sign = inches < 0 ? '-' : '';
  const eighths = Math.round(Math.abs(inches) * 8);
  const feet = Math.floor(eighths / 96);
  const rem = eighths - feet * 96;
  const whole = Math.floor(rem / 8);
  const frac = EIGHTHS[rem % 8];
  const inch = whole || !frac ? `${whole}${frac}` : frac.trim();
  return feet ? `${sign}${feet}'-${inch}"` : `${sign}${inch}"`;
}

export const metresToFtIn = (m) => ftIn(m / IN);

/** glTF world (x east, y up, z south) -> room drawing coordinates in inches (x east, y north, z up). */
export function roomCoords(v) {
  return { x: v.x / IN, y: -v.z / IN, z: v.y / IN };
}

export function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export const isTouch = () => matchMedia('(pointer: coarse)').matches;
