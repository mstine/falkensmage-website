# falkensmage.com — Site Specification

## What This Is

Single-page, mobile-first personal site for Matt Stine's public identity: **Falken's Mage**.

This is the front door. Social discovery lands here. Everything else orbits it.

- **Feral Architecture** (Substack) is what people find inside.
- **Digital Intuition** is the LLC.
- **Falken's Labyrinth** is the book.
- **RitualSync** is the software company (TarotPulse, etc.).

The site does one thing: make the person legible in ten seconds on a phone screen.

## Voice

"Technomagickal motherfucker." Public-facing, no softening, no register shift. The site should feel like the person who writes Feral Architecture — direct, alive, irreverent, holding paradox without apology.

## Hero Image

The cover from "Aesthetic Decisions are Architecture Decisions" — the Magus at the desk with wand raised, laptop open, tarot cards in hand, raven on the shelf, lemniscate sigil overhead.

Source: `~/Documents/Business-Brand/Feral-Architecture/covers/2026-04-14-aesthetic-decisions/final/aesthetic-decisions-cover.jpg`

This image is 1200x628 (Substack/OG horizontal). For the site hero, consider:
- Full-bleed on mobile with content overlaid or below
- Cropped/zoomed for portrait orientation on mobile
- Original aspect on desktop with content beside or below

## Color Palette — ARCÆON System

### Primary Identity (branding, text accents, interactive elements)
- Electric Violet: `#7a2cff`
- Neon Magenta: `#ff3cac`
- Electric Blue: `#2fd3ff`

### Focal Energy (glow, highlights, transformation moments)
- Solar White: `#fff4e6`
- Fusion Gold: `#ffb347`
- Ignition Orange: `#ff7a18`

### Cosmic Depth (backgrounds, grounding, contrast)
- Deep Indigo: `#0a0f3c`
- Midnight Blue: `#111a6b`
- Void Purple: `#1a0f2e`

### Energy Accents
- Ion Glow: `#5be7ff`
- Plasma Pink: `#ff5fd2`

### The Triad Rule
Every section needs: one purple + one blue + one warm core = ARCAEON signature.

### Usage
- Backgrounds: Deep Indigo or Void Purple
- Primary text: Solar White `#fff4e6` (warm white, not pure white)
- Accent text / links: Ion Glow `#5be7ff` or Electric Violet `#7a2cff`
- Hover / active states: Neon Magenta `#ff3cac`
- CTA glow: Fusion Gold `#ffb347` → Ignition Orange `#ff7a18` gradient
- Subtle borders / dividers: Electric Violet at low opacity

## Page Structure

One page. Five sections. Vertical scroll.

### 1. Hero
- Magus image (full-width or near-full-width)
- Name: **Falken's Mage** (display treatment — large, typographic presence)
- Tagline: TBD — something sharp that encodes "enterprise architect + witch + AI builder + coach" without listing those words. Placeholder until Matt writes it.
- Subtle ambient animation: glow pulse on the image, particle drift, or similar. Nothing distracting. The image should feel alive, not static.

### 2. Identity Statement
- 2-3 sentences max. Who is this person and why should you care.
- Written in Matt's voice, not a third-person bio.
- This is the "technomagickal motherfucker" energy distilled into prose.

### 3. Social Links
- Linktree-style grid or vertical stack
- Each link: icon + label + subtle hover animation
- Links (known):
  - **Feral Architecture** — Substack (feralarchitecture.substack.com)
  - **LinkedIn** — linkedin.com/in/mattstine
  - **X** — https://x.com/falkensmage
  - **Instagram** — https://www.instagram.com/falkensmage
  - **Threads** — https://www.threads.com/@falkensmage
  - **Bluesky** — https://bsky.app/profile/falkensmage.bsky.social
  - **Spotify** — https://open.spotify.com/album/6v081tJ7Gqe77Lja7LuiOd?si=OQyLl6EgTVCfrvC9cubIvA
  - **TarotPulse** — https://my.tarotpulse.com
  - **Podcast** — TBD - not launched yet
- Matt to confirm exact URLs and which platforms to include/exclude.

### 4. Work With Me
- Brief (1-2 sentences): what Matt offers — coaching, speaking, collaboration.
- Single CTA: `mailto:falkensmage@falkenslabyrinth.com`
- Styled as a button with the Radiant Core glow treatment.
- No scheduling widget, no intake form. Just the email. Keep it sovereign.

### 5. Footer
- "Stay feral, folks." (signature closing)
- Copyright: Digital Intuition LLC
- Minimal. No nav repetition. Maybe a faint sigil or lemniscate mark.

## Technical Requirements

### Stack
- **Hugo** (https://gohugo.io/) — static site generator
- Custom Hugo theme: **arcaeon** — built from scratch, no third-party theme dependency
- HTML templates + CSS + minimal JS within Hugo's layout system
- Static output hosted on GitHub Pages (repo: falkensmage-website)
- GitHub Actions for build/deploy pipeline (hugo build → deploy to Pages)

### Why Hugo
- Matt has prior Hugo experience — no ramp-up cost
- Single-page works beautifully now; partials, sections, and content types are ready when the site grows
- Templating keeps the ARCÆON palette and component patterns DRY across future pages
- Static output means zero runtime dependencies, same performance profile as hand-crafted HTML
- Content as markdown files — future "Currently" section, blog posts, or additional pages are just new .md files
- Hugo's asset pipeline handles image optimization (WebP generation, resizing) without external tooling

### The `arcaeon` Theme

The theme is the brand. It's not a skin applied to content — it's the aesthetic contract enforced at the infrastructure level, the same way `TEMPLATE.md` enforces the Feral Architecture cover aesthetic.

**What the theme owns:**
- **CSS custom properties** — the full ARCÆON palette as design tokens (`--void-purple`, `--ion-glow`, `--neon-magenta`, etc.) so every component inherits the palette without hardcoded hex values
- **Typographic hierarchy** — display, heading, body, and accent type scales with consistent rhythm
- **Glow treatments** — reusable CSS for the signature ambient glow (CTA buttons, hover states, hero image pulse)
- **Dark graphic novel feel** — the chiaroscuro lighting aesthetic translated into web: deep backgrounds, directional light via gradients, painted shadow shapes
- **Sigil grammar** — subtle visual DNA from the Feral Architecture visual vocabulary (broken geometric circles, void-to-glow gradients, wound-seam composition) as decorative elements, not literal logo placement
- **Component partials** — hero, social-links, identity-statement, cta-block, footer as reusable Hugo partials
- **Responsive foundation** — mobile-first breakpoints baked into every partial, not bolted on after

**Why this matters for scaling:**
The theme becomes shared infrastructure. When Digital Intuition, Falken's Labyrinth (book teaser), or future properties need a web presence, they can either:
1. Use the `arcaeon` theme directly with different content and configuration (same palette, different identity)
2. Fork it as a starting point with intentional divergence (RitualSync pulling from the Radiant Core tier)

Every new page, section, or site built on this theme inherits the brand without requiring design decisions — just content decisions. The theme is the guardrail that keeps the visual ecosystem coherent as it grows.

### Performance
- Single page load under 1s on 3G
- Hero image optimized (WebP with JPEG fallback, lazy-load below fold)
- No external fonts unless self-hosted (consider system font stack or a single self-hosted face)
- No analytics unless Matt explicitly adds them later

### Mobile-First
- Designed for 375px viewport first, scales up
- Touch targets minimum 44px
- Social links must be easily thumb-reachable
- Hero image must work in portrait orientation
- No horizontal scroll. Ever.

### Accessibility
- Semantic HTML5
- Color contrast ratios meet WCAG AA against dark backgrounds
- All images have meaningful alt text
- Social links have aria-labels
- Respects prefers-reduced-motion for any animations

### SEO / Meta
- Open Graph tags with Magus image
- Twitter card meta
- Proper title: "Falken's Mage — Matt Stine"
- Meta description that encodes the identity
- Canonical URL: https://falkensmage.com

### Domain
- falkensmage.com — owned, needs DNS pointed to GitHub Pages
- HTTPS via GitHub Pages (automatic with custom domain)

## What This Is NOT

- Not a CRM or email capture tool (that's the sovereign stack project)
- Not a content platform (Feral Architecture on Substack handles that)
- Not a full offer stack with scheduling/payment (premature — ICP still being refined)
- Not a portfolio or resume site
- Not a Linktree clone — it has a Linktree-style section, but the hero and identity framing make it a proper site

## Open Items

- [ ] Tagline — Matt needs to write the one-liner
- [x] Social URLs — confirm exact handles for X, Instagram, Threads, Bluesky
- [x] Spotify link — direct album URL or artist profile?
- [ ] Podcast link — Rewired feed URL or holding page?
- [x] TarotPulse URL — confirm current live URL
- [ ] Typography — font selection (or commit to system stack)
- [ ] Favicon — sigil mark? Lemniscate? Something from the Feral Architecture visual grammar?
- [ ] Whether to include a "Currently" section (latest Feral Arch post, current project, etc.) — adds dynamism but requires maintenance or automation

## Reference Material

- ARCAEON palette full system: `~/.psyche/swipe-files/podcasting-creative/2026-04-16-12-33-18-arc-on-color-palette-full.md`
- Feral Architecture aesthetic contract: `~/Documents/Business-Brand/Feral-Architecture/covers/TEMPLATE.md`
- Brand architecture thread: Brand Website — Own the Stack (psyche-threads)
- Brand hierarchy thread: Techno-Mysticism Brand Launch — Next Moves (psyche-threads)
