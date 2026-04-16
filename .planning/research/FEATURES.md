# Feature Research

**Domain:** Personal brand single-page identity site (social discovery front door, not portfolio/blog/offer stack)
**Researched:** 2026-04-16
**Confidence:** HIGH

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a stranger landing from social expects. Missing any of these creates a "did they even care?" read that kills credibility in seconds.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Hero section with image + name | Every identity site has this. Absent = no anchor, user bounces immediately. | LOW | Portrait orientation for mobile-first; Magus image needs art direction for 375px. |
| Identity statement (bio) | User needs to know who this is in 2-3 sentences. The "ten second legibility" test lives here. | LOW | Must be first-person, in voice — not a LinkedIn summary. |
| Social links | Why they came. Social discovery expects to hop to the next surface. Missing = dead end. | LOW | Icon + label, not just icon. Hover state expected. Grid or stack layout both work. |
| Contact / reach out path | No contact = no credibility. The implicit ask: "how do I work with you?" | LOW | mailto link is sufficient at this scale. Full form is over-engineering. |
| Mobile-first layout | 70%+ of social discovery traffic is mobile. Broken mobile = broken site. | MEDIUM | 375px designed first. 44px touch targets. No horizontal scroll. |
| Fast load | Users expect sub-2s. Sub-1s on 3G is the actual constraint given social traffic sources. | MEDIUM | Static site solves this. WebP + lazy load below fold. No external font CDNs. |
| Open Graph / social preview | When the link gets shared, the preview is the ad. Missing OG = ugly unfurl, kills resharing. | LOW | Title, description, Magus image. Twitter card. Canonical URL. |
| Favicon | Tiny but noticed when absent. Tab identity. | LOW | Lemniscate sigil. |
| Accessible markup | WCAG AA is the floor. Broken accessibility = broken on screen readers and some mobile browsers. | LOW | Semantic HTML5, meaningful alt text, aria-labels, prefers-reduced-motion. |
| HTTPS + custom domain | http:// in 2026 reads as abandoned project. Generic subdomain reads as "link in bio" not personal brand. | LOW | GitHub Pages handles HTTPS automatically. Domain is owned. |

### Differentiators (Competitive Advantage)

What separates a real brand presence from a Linktree with a custom color. These are where falkensmage.com earns its identity as a front door, not just a directory.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dark graphic novel aesthetic (ARCÆON system) | 99% of personal brand sites use safe generic design. A fully realized dark neon palette with glow treatments signals that this person is not doing generic. Strangers notice. | HIGH | ARCÆON CSS custom properties as infrastructure. Triad rule per section. Glow buttons. This IS the brand — not decoration applied to a template. |
| Ambient animation (targeted, not heavy) | Subtle motion in the hero creates presence without performance penalty. Static dark sites feel cold; animated ones feel alive. Industry moving toward lightweight targeted animation specifically. | MEDIUM | CSS-only where possible. prefers-reduced-motion honored. Single ambient effect, not a particle system. |
| Voice-first identity statement | Most personal sites produce LinkedIn summaries. A first-person statement that sounds like the person — irreverent, direct, "technomagickal motherfucker" energy — is rare and memorable. Strangers who get it, stay. Those who don't weren't the audience. | LOW | Complexity is in the writing, not the implementation. Copy must be written before phase executes. |
| "Currently" section with live RSS pull | Most Linktree-style pages are static. A dynamically pulled latest Substack post signals active creator — keeps the page from feeling abandoned even when Matt isn't manually updating. Paired with a manually editable current focus blurb. | MEDIUM | Hugo can template RSS fetch at build time. GitHub Actions triggers on schedule or push. The "now page" pattern (Derek Sivers / nownownow.com) is an established IndieWeb convention that sophisticated audiences recognize and trust. |
| Sigil / lemniscate brand mark | Most personal sites use a photo as the only visual identity anchor. A crafted sigil as favicon + footer mark ties the visual system together and carries symbolic weight consistent with the brand voice. Rare in this space. | LOW | SVG. Reusable across Digital Intuition properties. |
| "Work With Me" glow CTA | Most coaching CTAs are generic buttons. A single Radiant Core glow treatment on the primary CTA makes the ask feel like the site wanted you to click it — not like it was placed there because CTAs exist. | LOW | One CTA, not five. Complexity is in the visual treatment, not the pattern. |
| Typography that carries the aesthetic | System stacks don't convey dark graphic novel. A self-hosted typeface selected specifically for the ARCÆON aesthetic turns the reading experience into a brand signal. | MEDIUM | Research required to select face(s). Self-hosting avoids CDN penalty. Decision pending. |
| Closing signature in voice | "Stay feral, folks." in the footer — a line that sounds like the person — signals to anyone who scrolled this far that the whole page was authored, not generated. | LOW | One line. Zero complexity. High signal. |

### Anti-Features (Deliberately NOT Building)

Things that look like upgrades but would break the concept.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Email capture / newsletter signup | "You should be growing your list from day one." | Sovereign stack project handles this. Adding it here creates a competing destination and a maintenance dependency on an external service before ICP is refined. Premature capture without a clear follow-up sequence is spam bait. | When the sovereign stack is ready, the CTA can point there. Not yet. |
| Analytics | "How do you know what's working?" | Adds external dependency, slows load, creates GDPR surface. At this stage, "working" means "site exists and sounds like Matt." There's no conversion funnel to optimize. | Add when there's a specific behavior to measure. Not a launch requirement. |
| Full offer stack (scheduling, payment) | "While you're building it, add the booking page." | ICP is still being refined. Premature offer architecture locks in assumptions that may be wrong. Adds complexity that conflicts with sub-1s load constraint. | Work with Me is a mailto. Enough for now. |
| Portfolio / case studies | "Prove your credibility with past work." | This is an identity site, not a credentials site. Case studies require maintenance, confidentiality judgment calls, and shift the frame from "who is this person" to "what have they done." Wrong register. | Feral Architecture Substack is the living proof of work. Link to it. |
| Blog / content hub | "Centralize your content." | Content lives on Substack. Duplicating or replacing it adds publishing workflow overhead and splits the audience. The RSS pull in "Currently" is the right bridge — signals active creator without competing. | Substack handles this. |
| Podcast player embed | "You have a podcast, add it." | Rewired isn't live yet. Dead embed or empty player destroys credibility faster than absence. | Add the Spotify link once the feed is live. |
| OAuth / login / user accounts | "What if you want to add members-only content?" | This is a static public page. The moment authentication enters the picture, the architecture changes completely. Wrong conversation for this phase. | Not this site. |
| Testimonials / social proof | "Add credibility." | Coaching offer is not formalized. Generic testimonials without context rarely change behavior. Placement before the offer is defined is premature. | Add when there's a specific offer to validate. |
| Multi-page navigation | "You'll want to expand later." | Single-page is the entire concept. Multi-page turns a front door into a website. Different job. | If expansion is needed, it's a different project. |

---

## Feature Dependencies

```
[ARCÆON CSS system]
    └──required by──> [Hero section visual treatment]
    └──required by──> [Glow CTA button]
    └──required by──> [Dark aesthetic ambient animation]
    └──required by──> [Typography hierarchy]
    └──required by──> [All section layouts]

[Self-hosted typography decision]
    └──required by──> [Full ARCÆON typographic hierarchy]

[Hugo theme `arcaeon`]
    └──required by──> [RSS pull for "Currently" section]
    └──required by──> [Image optimization pipeline (WebP)]
    └──required by──> [All component partials]

[GitHub Actions pipeline]
    └──required by──> [RSS pull refresh on schedule]
    └──required by──> [GitHub Pages deploy]

[Magus image art direction]
    └──required by──> [Hero section mobile portrait layout]
    └──required by──> [Open Graph preview image]

[Identity statement copy]
    └──required by──> [Hero / bio section implementation]
    └──written before──> [Phase executes — not a build dependency]

[Lemniscate sigil SVG]
    └──required by──> [Favicon]
    └──required by──> [Footer brand mark]
```

### Dependency Notes

- **ARCÆON CSS system is the root dependency.** Everything visual depends on it being defined first as custom properties. Build this before any section layout.
- **Typography decision gates the typographic hierarchy.** Font selection research must complete before `arcaeon` theme establishes its type scale.
- **Magus image art direction gates the hero.** The existing image (1200x628 horizontal) needs to be assessed for mobile portrait crop before the hero section is built.
- **RSS pull depends on Hugo theme structure.** Can't implement "Currently" until the template partial system is in place.
- **Identity statement copy is a human dependency, not a build dependency.** The slot can be built with placeholder text, but the real line has to be written by Matt before launch.

---

## MVP Definition

### Launch With (v1)

Minimum that makes the front door real. Every item here is load-bearing for the "ten second legibility" test.

- [ ] Hugo `arcaeon` theme with ARCÆON CSS system — the foundation everything else sits on
- [ ] Hero section: Magus image (art-directed for mobile), "Falken's Mage" display treatment, placeholder tagline slot — first thing they see
- [ ] Identity statement — 2-3 sentences in voice, first-person — answers "who is this person"
- [ ] Social links section — all eight platforms, icon + label, hover states — why they came
- [ ] "Work With Me" section — coaching/speaking/collaboration framing, mailto CTA with Radiant Core glow treatment — how to reach Matt
- [ ] "Currently" section — RSS-pulled latest Feral Architecture post + manually editable current focus blurb — signals active creator
- [ ] Footer — "Stay feral, folks." + Digital Intuition LLC copyright + lemniscate mark — completes the voice
- [ ] Self-hosted typography (face selected via research) — carries the dark graphic novel aesthetic
- [ ] Lemniscate sigil favicon
- [ ] Open Graph / Twitter card meta — social preview when links get shared
- [ ] Ambient animation in hero (CSS-only, prefers-reduced-motion honored) — presence without performance penalty
- [ ] GitHub Actions build/deploy to GitHub Pages
- [ ] WCAG AA accessibility baseline, semantic HTML5
- [ ] Sub-1s load on 3G, WebP with JPEG fallback

### Add After Validation (v1.x)

These are additions triggered by evidence, not assumptions.

- [ ] Analytics (Fathom or similar, privacy-first) — add when there's a specific behavior to measure
- [ ] Spotify / podcast link — add when Rewired feed is live
- [ ] Testimonials — add when coaching offer is formalized and specific proof points exist
- [ ] Email capture CTA — add when sovereign stack is ready to receive subscribers

### Future Consideration (v2+)

- [ ] Offer expansion (speaking page, coaching intake form) — when ICP is refined and offer is validated
- [ ] Dark/light mode toggle — if there's evidence the audience wants it; ARCÆON is a dark-first system

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| ARCÆON CSS system | HIGH | MEDIUM | P1 |
| Hugo `arcaeon` theme + pipeline | HIGH | MEDIUM | P1 |
| Hero section (image + name + tagline) | HIGH | LOW | P1 |
| Identity statement copy | HIGH | LOW | P1 |
| Social links section | HIGH | LOW | P1 |
| Open Graph meta | HIGH | LOW | P1 |
| Mobile-first responsive layout | HIGH | MEDIUM | P1 |
| Self-hosted typography | HIGH | MEDIUM | P1 |
| "Work With Me" CTA (mailto + glow) | HIGH | LOW | P1 |
| "Currently" RSS + manual blurb | MEDIUM | MEDIUM | P1 |
| Ambient animation (hero) | MEDIUM | LOW | P1 |
| Lemniscate favicon + footer mark | MEDIUM | LOW | P1 |
| Footer voice signature | MEDIUM | LOW | P1 |
| Accessibility baseline | HIGH | LOW | P1 |
| Analytics | LOW | LOW | P3 |
| Email capture | LOW | LOW | P3 |
| Testimonials | LOW | LOW | P3 |
| Podcast link | LOW | LOW | P2 (trigger: feed live) |

---

## Competitor Feature Analysis

| Feature | Linktree | Carrd | A-list creator sites (e.g. Austin Kleon, Derek Sivers) | falkensmage.com approach |
|---------|----------|-------|------------------------------------------------------|--------------------------|
| Custom domain | Paid only | Yes ($9/yr) | Yes | Yes — owned |
| Design control | Minimal | Moderate | Full | Full — theme IS the brand |
| Social links | Core feature | Manual | Manual | Manual — icon + label + hover |
| Identity statement | No | Copy block | Yes — often strong voice | Yes — in voice, first-person |
| Dynamic/live content | No | No | Occasionally (/now pages) | Yes — RSS pull from Substack |
| Dark aesthetic | Limited | Limited | Varies | ARCÆON system — full commitment |
| Custom animation | No | No | Rare | Targeted CSS ambient — hero only |
| "Now/Currently" section | No | No | Yes (established IndieWeb pattern) | Yes — RSS + manual blurb |
| Voice-driven footer signature | No | No | Sometimes | Yes — "Stay feral, folks." |
| Performance target | Fast (hosted) | Fast | Varies | Sub-1s on 3G, static |
| CMS dependency | Platform | Carrd | Varies | None — Hugo static |

---

## Sources

- [Personal Websites: 35 Inspiring Examples (2026)](https://www.sitebuilderreport.com/inspiration/personal-websites)
- [20 Powerful Personal Brand Websites That Convert (2026)](https://colorlib.com/wp/personal-brands/)
- [Top Landing Page Layouts That Convert in 2026](https://me-page.com/blog/design-and-templates/top-landing-page-layouts-that-convert-in-2026)
- [Vivid Glow Aesthetics: Bright Colors & Light Effects in 2025 Web Design](https://ecommercewebdesign.agency/vivid-glow-aesthetics-how-bright-colors-and-light-effects-define-2025-web-design/)
- [Dark Mode Web Design in 2025: UX, SEO & Design Tips](https://designindc.com/blog/dark-mode-web-design-seo-ux-trends-for-2025/)
- [Framer Blog: 7 emerging web design trends for 2025](https://www.framer.com/blog/web-design-trends/)
- [The /now page — Derek Sivers](https://sive.rs/now2)
- [now — IndieWeb](https://indieweb.org/now)
- [nownownow.com](https://nownownow.com/)
- [Best Linktree Alternatives 2026 — ecomm.design](https://ecomm.design/linktree-alternatives/)
- [Personal Brand Website Strategy 2026 — Unicorn Platform](https://unicornplatform.com/blog/personal-brand-website-strategy-in-2026/)

---
*Feature research for: personal brand single-page identity site (falkensmage.com)*
*Researched: 2026-04-16*
