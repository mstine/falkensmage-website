---
phase: 01-theme-foundation
plan: 02
subsystem: css
tags: [typography, fonts, glow-system, animation, accessibility]
dependency_graph:
  requires: [01-01]
  provides: [typography-section, glow-system-section]
  affects: [themes/arcaeon/assets/css/main.css]
tech_stack:
  added: []
  patterns:
    - "@font-face with font-display: swap for FOIT prevention"
    - "Minor Third type scale (1.2 ratio) with clamp() display treatment"
    - "::before + opacity GPU-composited glow pattern (no box-shadow)"
    - "prefers-reduced-motion: reduce wrapping every animation/transition"
key_files:
  created: []
  modified:
    - themes/arcaeon/assets/css/main.css
decisions:
  - "font-weight ranges declared as '400 900' (Cinzel) and '300 700' (Space Grotesk) matching variable font axis ranges from @fontsource-variable packages"
  - "::before reserved for glow effects, ::after reserved for sigils — consistent pseudo-element convention"
  - "will-change: opacity on all glow ::before elements for GPU layer promotion on mobile"
requirements-completed: [THEME-02, THEME-03]
metrics:
  duration: "82 seconds"
  completed: "2026-04-16"
  tasks: 2
  files: 1
---

# Phase 01 Plan 02: Typography and Glow System Summary

**One-liner:** Self-hosted Cinzel Variable + Space Grotesk Variable @font-face declarations, Minor Third type scale, and three GPU-composited glow variants (ambient pulse, interactive, Radiant Core CTA) — all with prefers-reduced-motion support.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add Typography section to main.css | fb857ad | themes/arcaeon/assets/css/main.css |
| 2 | Add Glow System section to main.css | 5e6f736 | themes/arcaeon/assets/css/main.css |

## What Was Built

**Typography section:**
- Two `@font-face` declarations with `font-display: swap` — Cinzel Variable (weights 400–900) and Space Grotesk Variable (weights 300–700)
- Font URL paths use `../fonts/` relative to `assets/css/` — verified against actual files in `assets/fonts/`
- CSS custom properties: `--font-display`, `--font-heading`, `--font-body` on `:root`
- Minor Third scale (1.2 ratio): `--text-base: 1rem`, `--text-h3: 1.44rem`, `--text-h2: 1.728rem`, `--text-h1: 2.074rem`, `--text-display: clamp(2.5rem, 8vw, 4rem)`
- Weight progression: `--weight-display: 800`, `--weight-h1: 700`, `--weight-h2: 600`, `--weight-h3: 500`
- Element styles: `body` (Space Grotesk, 400, line-height 1.6), `h1/h2/h3` (Cinzel with weight progression), `a` / `a:hover`, `.display-text` utility class

**Glow System section (three variants):**
- `.glow-ambient` — 5s ease-in-out breathing cycle on `::before`, Electric Violet radial gradient, opacity oscillates 0.2–0.5. Reduced-motion: animation disabled, opacity static 0.3.
- `.glow-interactive` — `::before` starts at opacity 0, transitions to 0.6 on `:hover` / `:focus-visible` (0.25s ease). Electric Violet. Reduced-motion: transition removed.
- `.glow-radiant-core` — Fusion Gold to Ignition Orange gradient button. `::before` warm radial glow at opacity 0 → 0.7 on hover (0.3s ease). Reduced-motion: transition removed.

All glow variants: `pointer-events: none`, `will-change: opacity`, `z-index: -1`, `::before` only (never `::after`). Zero `box-shadow` declarations in entire stylesheet.

## Verification Results

| Check | Result |
|-------|--------|
| `hugo --minify` exit code | 0 |
| `@font-face` declarations | 2 |
| `font-display: swap` (inline) | 2 |
| `prefers-reduced-motion` blocks | 4 (1 existing reset + 3 glow) |
| `box-shadow` count | 0 |
| `.glow-ambient` present | yes |
| `.glow-interactive` present | yes |
| `.glow-radiant-core` present | yes |
| Font URL paths match actual files | yes |

## Deviations from Plan

None — plan executed exactly as written. Font filenames matched expected names (`cinzel-latin-wght-normal.woff2`, `space-grotesk-latin-wght-normal.woff2`). baseof.html preload links already used correct filenames — no update needed.

## Known Stubs

None. This plan populates content; it does not introduce placeholder values that flow to rendering.

## Threat Flags

None. CSS-only changes, no new network endpoints, no auth paths, no schema changes.

## Self-Check: PASSED

- `themes/arcaeon/assets/css/main.css` — FOUND and modified
- Commit fb857ad (Task 1) — FOUND
- Commit 5e6f736 (Task 2) — FOUND
- `hugo --minify` — exits 0
