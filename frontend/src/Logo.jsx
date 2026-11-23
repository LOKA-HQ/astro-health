import React from 'react';

// Theme-aware Astro Health logo. The mark is inline SVG and its colors come
// from CSS (.logo-* rules in style.css), so it adapts to the dark/light theme.
// The pulse line is drawn twice: once in the theme's line color, once clipped
// to the planet in the contrasting color, so it stays readable on both the
// badge background and the planet.
export default function Logo() {
  const pulse = '12,32 22,32 26,23 31,41 35,29 38,32 52,32';
  return (
    <svg className="brand-logo" viewBox="0 0 64 64" role="img" aria-label="Astro Health logo">
      <defs>
        <clipPath id="logo-planet-clip">
          <circle cx="32" cy="32" r="10" />
        </clipPath>
      </defs>
      <rect className="logo-bg" x="0.5" y="0.5" width="63" height="63" rx="15" />
      <ellipse
        className="logo-orbit"
        cx="32"
        cy="32"
        rx="25"
        ry="9.5"
        transform="rotate(-24 32 32)"
      />
      <circle className="logo-planet" cx="32" cy="32" r="10" />
      <polyline className="logo-pulse" points={pulse} />
      <polyline className="logo-pulse-in" points={pulse} clipPath="url(#logo-planet-clip)" />
      <circle className="logo-sat" cx="54" cy="22" r="2.6" />
    </svg>
  );
}
