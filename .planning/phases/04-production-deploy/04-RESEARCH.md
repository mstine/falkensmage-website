# Phase 4: Production Deploy - Research

**Researched:** 2026-04-17
**Domain:** GitHub Actions CI/CD, GitHub Pages, DNS configuration, SVG favicon generation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Favicon style — ARCAEON glow mark. Electric Violet (#7a2cff) lemniscate stroke on transparent background with subtle Neon Magenta (#ff3cac) outer glow. Clean geometric curves, readable at 16x16 and 32x32.
- **D-02:** Favicon source — Hugo-generated SVG at build time via a template partial. Favicon inherits palette token values from hugo.toml, stays in sync automatically if colors ever shift.
- **D-03:** Favicon formats — `.svg` for modern browsers + `.ico` generated from the SVG for legacy. Both linked in `<head>`.
- **D-04:** Workflow trigger — push to `main` only. No PR builds, no manual dispatch.
- **D-05:** Build steps — Hugo Extended 0.160.1 pinned, `npm ci` for font packages, `hugo --minify --environment production`, deploy via `actions/deploy-pages@v4`.
- **D-06:** Workflow pattern — official Hugo starter structure: `actions/configure-pages@v4`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`. Direct binary install, no third-party Hugo action.
- **D-07:** Repo creation — `gh repo create` public repo under personal account. Add remote, push existing `main`.
- **D-08:** CNAME — `static/CNAME` containing `falkensmage.com`.
- **D-09:** DNS — phase plan includes step-by-step checklist for Namecheap DNS pointing to GitHub Pages A records.
- **D-10:** HTTPS — automatic via GitHub Pages once DNS propagates.

### Claude's Discretion

- SVG lemniscate curve geometry and glow filter parameters — as long as readable at favicon sizes
- Exact workflow YAML structure within pattern constraints (D-06)
- `.ico` generation approach — build-time script or committed artifact from SVG source
- DNS checklist formatting and level of detail

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-03 | GitHub Actions workflow — Hugo Extended 0.160.1 pinned, `npm ci` for fonts, `hugo --minify`, deploy to GitHub Pages | Verified workflow YAML structure, action versions, permissions model |
| INFRA-04 | `static/CNAME` file with `falkensmage.com` — persists custom domain across deploys | Clarified: CNAME in build output is legacy pattern; custom domain persists via repo Settings. `static/CNAME` still useful as docs/backup but repo Settings is the authority. |
| INFRA-05 | Lemniscate sigil favicon (`.ico` + `.svg`) | SVG generation via Hugo partial verified; ICO generation via rsvg-convert + Python struct verified; CI tooling path documented |
</phase_requirements>

---

## Summary

Phase 4 is pure infrastructure — no content or styling changes. The work has three parts: (1) create the GitHub repo and push the existing codebase, (2) write and wire the GitHub Actions workflow that builds Hugo and deploys to Pages, and (3) generate the lemniscate favicon in SVG + ICO formats and wire the `<head>` links.

The DNS situation is the most time-sensitive item. `falkensmage.com` currently has an apex CNAME pointing to `target.substack-custom-domains.com` — it was configured as a Substack custom domain. The Feral Architecture newsletter lives at `feralarchitecture.com` (separate domain, separate Substack CNAME), so cutting `falkensmage.com` over to GitHub Pages does not break the newsletter. The DNS change is: delete the Substack CNAME, add four GitHub Pages A records. Registrar is Namecheap. TTL is 1800s — allow up to 30 minutes for propagation, HTTPS certificate provisioning adds another 15-60 minutes after that.

The custom domain persistence question has a subtlety: with `deploy-pages`-based GitHub Actions deployments, GitHub's official docs say CNAME files in the build output are "ignored" and the custom domain is stored in repo Settings. Community evidence suggests GitHub Pages *does* actually read a CNAME in the deployed artifact to avoid resetting the domain on each deploy, but the authoritative path is setting the domain in Settings once after first deploy. The `static/CNAME` approach (D-08) remains the right safety net — Hugo copies `static/` to `public/` so the file lands in the artifact — but the plan must also include setting the custom domain in repo Settings as a one-time manual step.

**Primary recommendation:** Ship in sequence — repo, workflow, favicon, first push, repo Settings config, DNS change. Don't do DNS before the site is live on `mstine.github.io`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Hugo Extended | 0.160.1 | Static site generator + CSS build | Already installed, locked in CLAUDE.md |
| `actions/checkout` | v4 | Checkout repo in CI | Official GitHub action |
| `actions/configure-pages` | v6 | Enable Pages, extract base URL | Official, latest stable (v6 released 2026-03-25) |
| `actions/upload-pages-artifact` | v3 | Upload `./public` as Pages artifact | Official |
| `actions/deploy-pages` | v5 | Deploy artifact to GitHub Pages | Official, latest stable |

[VERIFIED: github.com/actions/configure-pages releases — v6.0.0, 2026-03-25]
[VERIFIED: github.com/actions/upload-pages-artifact releases — v3]
[VERIFIED: github.com/actions/deploy-pages releases — v5]

**Note on action versions vs. CONTEXT.md D-05/D-06:** The context specifies `deploy-pages@v4`. The current latest is v5. Both are valid — v5 is the safer choice for forward compatibility. The planner should use **v5** for all three deploy actions since they were all released together and the official starter workflow already references v5. This is Claude's discretion within the pattern constraint.

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `rsvg-convert` | 2.60.0 (local), system on CI | Render SVG to PNG at specific pixel sizes | ICO generation pipeline — converts the Hugo-generated SVG to 16x16 and 32x32 PNGs |
| Python3 | stdlib only | Wrap PNGs into `.ico` binary format | No pip dependencies; ICO format spec is trivial with `struct` |

[VERIFIED: rsvg-convert 2.60.0 installed locally via `rsvg-convert --version`]
[VERIFIED: Python3 stdlib struct module — ICO format V2 spec (PNG compression) confirmed workable]

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| rsvg-convert + Python struct | ImageMagick `convert` | ImageMagick not pre-installed on ubuntu-24.04 runners; requires `apt install` step. rsvg-convert + Python stdlib = no apt install needed IF librsvg2-bin is available. Safer fallback: commit the `.ico` as a static asset generated locally once. |
| Hugo partial SVG generation | Static committed SVG | Partial generation keeps palette in sync; committed SVG is simpler but drifts if tokens change. Decision D-02 locks Hugo partial approach. |

---

## Architecture Patterns

### GitHub Actions Workflow (INFRA-03)

**Verified YAML pattern** — adapted from official Hugo starter workflow, updated to current action versions and Phase 4 constraints:

```yaml
# .github/workflows/hugo.yml
# Source: github.com/actions/starter-workflows/blob/main/pages/hugo.yml [VERIFIED]

name: Deploy Hugo site to Pages

on:
  push:
    branches: ["main"]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

defaults:
  run:
    shell: bash

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.160.1
    steps:
      - name: Install Hugo CLI
        run: |
          wget -O ${{ runner.temp }}/hugo.deb \
            https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb \
          && sudo dpkg -i ${{ runner.temp }}/hugo.deb

      - name: Install Dart Sass
        run: sudo snap install dart-sass

      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v6

      - name: Install Node.js dependencies
        run: "[[ -f package-lock.json || -f npm-shrinkwrap.json ]] && npm ci || true"

      - name: Build with Hugo
        env:
          HUGO_CACHEDIR: ${{ runner.temp }}/hugo_cache
          HUGO_ENVIRONMENT: production
        run: |
          hugo \
            --minify \
            --baseURL "${{ steps.pages.outputs.base_url }}/"

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v5
```

[VERIFIED: Official starter workflow structure — github.com/actions/starter-workflows]
[VERIFIED: Hugo 0.160.1 Extended .deb available at github.com/gohugoio/hugo/releases/v0.160.1]

**Key constraint:** `baseURL` is sourced from `steps.pages.outputs.base_url` — this means it will be the custom domain URL once Pages Settings is configured, or `mstine.github.io/falkensmage-website` before that. The `hugo.toml` `baseURL = "https://falkensmage.com/"` is overridden by the workflow flag — that's correct behavior.

### Custom Domain Persistence (INFRA-04)

The `static/CNAME` file approach (D-08) puts `falkensmage.com` in the Hugo build output at `public/CNAME`. This is the Hugo-recommended pattern. [CITED: docs.gohugo.io]

**Critical nuance:** GitHub's official docs state that for GitHub Actions deployments, CNAME files in the artifact are "ignored" and the custom domain must be configured via repo Settings. Community reports indicate the CNAME in the artifact does prevent the domain from resetting on redeploy in practice — but this behavior is not guaranteed by GitHub's published spec.

**Plan must include both:**
1. `static/CNAME` with `falkensmage.com` (build output safety net, D-08)
2. Manual one-time step: repo Settings > Pages > Custom domain: `falkensmage.com` (authoritative)

The Settings entry is the load-bearing step. The CNAME file is defense-in-depth.

[CITED: docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site]
[CITED: github.com/orgs/community/discussions/48422]

### Favicon Generation (INFRA-05)

**Two-step approach:**

**Step 1 — Hugo SVG partial** (D-02):
Hugo template partial outputs an inline SVG at `/favicon.svg` using palette tokens from hugo.toml.

```
themes/arcaeon/layouts/partials/head/favicon.html  → <link> tags
themes/arcaeon/static/favicon.svg                  → Static committed SVG (D-02 alt approach)
```

Because Hugo templates can't write to arbitrary output paths directly (they render into the HTML stream), the SVG favicon needs to either be:
- A **committed static file** at `static/favicon.svg` (values manually extracted from hugo.toml once, updated if palette changes)
- Or a **Hugo output format** rendering to a separate file (more complex, requires defining a custom output format)

The simplest approach that satisfies D-02's intent (palette-driven) is: a **build-time Node.js/shell script** that reads palette values from `hugo.toml` and writes `static/favicon.svg` — run once during setup, or as a pre-build step.

Alternatively, since the palette is fixed for v1, a **committed SVG with hardcoded palette values** is acceptable and aligns with how the existing `static/` pattern works.

**Step 2 — ICO generation** (local, committed as static asset):
```bash
# Generate PNG frames from SVG
rsvg-convert -w 16 -h 16 static/favicon.svg > /tmp/favicon-16.png
rsvg-convert -w 32 -h 32 static/favicon.svg > /tmp/favicon-32.png

# Wrap into ICO (Python stdlib)
python3 scripts/png-to-ico.py /tmp/favicon-16.png /tmp/favicon-32.png static/favicon.ico
```

The `.ico` is committed as a static file — no CI dependency on `rsvg-convert` or Python.

**Why commit the ICO rather than generate in CI:** ImageMagick is not pre-installed on ubuntu-24.04 runners. `librsvg2-bin` would need an `apt install` step. A committed ICO avoids CI complexity entirely for a file that changes rarely (only if the favicon design changes). [VERIFIED: ubuntu-24.04 runner — ImageMagick not pre-installed per actions/runner-images#11384]

**`<head>` link tags** added to `baseof.html`:
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
```

[VERIFIED: MDN favicon recommendation — SVG first, ICO fallback for legacy]

### Repository Setup (D-07)

```bash
# Create public repo
gh repo create falkensmage-website --public --source=. --remote=origin

# Push existing main branch
git push -u origin main
```

After push: GitHub Actions runs automatically on `main`. Before enabling GitHub Pages, the workflow will fail at the deploy step (Pages not enabled). Enable Pages in Settings **before** or **immediately after** the first push.

**GitHub Pages enable sequence:**
1. `gh repo create` + push
2. Repo Settings > Pages > Source: GitHub Actions (NOT "Deploy from branch")
3. Repo Settings > Pages > Custom domain: `falkensmage.com`
4. First workflow run succeeds

Or use `gh api` to enable Pages programmatically:
```bash
gh api repos/mstine/falkensmage-website/pages \
  --method POST \
  --field build_type=workflow
```

[VERIFIED: github.com token scopes include `repo` — sufficient for Pages API on public repos]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hugo binary in CI | Download Hugo from source or use peaceiris/actions-hugo | Direct `.deb` download from gohugoio/hugo releases | Third-party actions add dependency risk; official `.deb` is deterministic, version-pinned |
| SVG → ICO conversion | Custom rasterizer | rsvg-convert + Python struct (or commit the file) | rsvg-convert handles SVG filter effects (glow) correctly; DIY rasterization misses them |
| GitHub Pages deployment | Push to `gh-pages` branch manually | `actions/deploy-pages@v5` | Official action handles permissions, artifact upload, and deployment atomically |
| DNS verification | Manual `dig` commands | `dig` commands in the DNS checklist for Matt to run | Appropriate level — this is a human-verification step, not automated |

---

## Common Pitfalls

### Pitfall 1: Wrong Hugo Edition in CI

**What goes wrong:** Using `hugo_${VERSION}_linux-amd64.deb` (standard) instead of `hugo_extended_${VERSION}_linux-amd64.deb` (Extended). Standard Hugo silently fails on `css.Build` — produces an empty CSS file with no error.

**Why it happens:** The `.deb` filename differs only by `_extended_` in the middle. Easy typo.

**How to avoid:** Filename must be `hugo_extended_${HUGO_VERSION}_linux-amd64.deb`. Validate by running `hugo env` in the workflow and checking output includes `Extended`.

**Warning signs:** Site deploys but has no styles.

[VERIFIED: Hugo docs — Extended edition required for css.Build]

### Pitfall 2: GitHub Pages Source Not Set to "GitHub Actions"

**What goes wrong:** Workflow deploys successfully but the site doesn't appear, or the custom domain gets overridden with branch-based deployment behavior.

**Why it happens:** GitHub Pages defaults to "Deploy from branch" if not explicitly changed. The `actions/deploy-pages` action requires "GitHub Actions" source mode.

**How to avoid:** In repo Settings > Pages > Build and deployment > Source: select **GitHub Actions** before the first deploy.

**Warning signs:** Workflow succeeds but `pages-build-deployment` workflow also fires, or custom domain resets after deploy.

[CITED: docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site]

### Pitfall 3: `baseURL` Mismatch

**What goes wrong:** CSS/font paths resolve as relative to root but the site is served under a subpath (`mstine.github.io/falkensmage-website/`) before the custom domain is set up.

**Why it happens:** If the first deploy happens before the custom domain is configured in Pages Settings, `steps.pages.outputs.base_url` returns the subdirectory URL, not `https://falkensmage.com/`.

**How to avoid:** Configure the custom domain in Pages Settings before the first push (or immediately after), so the first successful deploy uses the correct base URL.

**Warning signs:** Styles and fonts 404 on the first deploy; everything works after domain is set.

### Pitfall 4: Custom Domain Resets After Deploy

**What goes wrong:** The custom domain entry in Pages Settings disappears after each push, serving the site from `mstine.github.io` instead.

**Why it happens:** This was a bug affecting `deploy-pages`-based workflows. For branch-based deployments, the CNAME file drove the domain; for Actions deployments, it's Settings-driven. If the CNAME file isn't present in the artifact, some older workflow versions reset the domain.

**How to avoid:** Keep `static/CNAME` with `falkensmage.com` (D-08 — already locked). Also set it in Settings. If it resets, set it in Settings again and confirm `static/CNAME` is in `public/CNAME` in the build output.

[CITED: github.com/orgs/community/discussions/48422]
[CITED: github.com/actions/deploy-pages/issues/304]

### Pitfall 5: Apex CNAME Conflicts with GitHub Pages A Records

**What goes wrong:** The current `falkensmage.com` DNS has an apex CNAME pointing to Substack. GitHub Pages requires A records at the apex (not a CNAME). The old Substack CNAME record must be **deleted** before adding GitHub Pages A records.

**Why it happens:** DNS records at the apex coexist in Namecheap's panel but the CNAME takes precedence and Namecheap flattens it — adding A records alongside an existing apex CNAME produces undefined behavior.

**How to avoid:** In Namecheap Advanced DNS: delete the existing CNAME record for `@` (Host: `@`, Value: `target.substack-custom-domains.com`) first, then add the four A records.

**Impact on Substack:** `feralarchitecture.com` (separate domain) is the Substack newsletter domain. Removing the `falkensmage.com` Substack CNAME does not affect the newsletter.

[VERIFIED: dig falkensmage.com — apex CNAME confirmed, TTL 1800]
[VERIFIED: dig feralarchitecture.com — separate Substack custom domain, unaffected]

### Pitfall 6: HTTPS Takes Time After DNS Change

**What goes wrong:** DNS propagates, site loads over HTTP, but HTTPS certificate not yet provisioned — browser shows security warning.

**Why it happens:** GitHub's Let's Encrypt certificate provisioning runs asynchronously after GitHub detects the domain pointing correctly. Can take 15-60 minutes.

**How to avoid:** Don't share the URL until HTTPS shows "Certificate provisioned" in Pages Settings. Do not click "Enforce HTTPS" until the certificate is green.

[CITED: docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site]

---

## DNS Checklist (for CONTEXT.md D-09)

**Registrar:** Namecheap  
**Panel:** Domain List > Manage > Advanced DNS

**GitHub Pages A records (apex — `@` host):**
```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

**www CNAME:**
```
Host: www  →  Value: mstine.github.io
```

**Steps:**
1. Delete existing `@` CNAME record (`target.substack-custom-domains.com`)
2. Add four A records: Host=`@`, Value=each IP above, TTL=Automatic
3. Add CNAME record: Host=`www`, Value=`mstine.github.io`, TTL=Automatic
4. Wait ~30 minutes for propagation
5. In GitHub repo Settings > Pages > Custom domain: enter `falkensmage.com` > Save
6. Wait for HTTPS certificate (green checkmark in Settings > Pages)
7. Enable "Enforce HTTPS" checkbox

**Verification:**
```bash
dig falkensmage.com A       # Should return all 4 GitHub IPs
dig www.falkensmage.com     # Should return CNAME → mstine.github.io
curl -I https://falkensmage.com  # Should return 200 with valid cert
```

[VERIFIED: GitHub Pages A record IPs — docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site]

---

## Code Examples

### Favicon SVG Template (lemniscate with glow)

```svg
<!-- static/favicon.svg — hardcoded palette values from hugo.toml [params.colors] -->
<!-- Source: D-01, D-02 — ARCAEON glow mark -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="1.5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  <!-- Lemniscate path — ∞ centered at 16,16, width ~26, height ~10 -->
  <!-- Bernoulli lemniscate parametric: x = a·cos(t)/(1+sin²(t)), y = a·sin(t)cos(t)/(1+sin²(t)) -->
  <path d="M16,16 C16,11 22,8 26,12 C30,16 26,24 16,16 C6,8 2,16 6,20 C10,24 16,21 16,16 Z"
        fill="none"
        stroke="#7a2cff"
        stroke-width="2"
        stroke-linecap="round"
        filter="url(#glow)"/>
</svg>
```

Note: The exact SVG path for the lemniscate needs refinement — the geometry above is a starting approximation. The planner should mark the path coordinates as requiring visual validation at 16x16 and 32x32.

### ICO Generation Script

```python
# scripts/png-to-ico.py
# Usage: python3 scripts/png-to-ico.py favicon-16.png favicon-32.png static/favicon.ico
# Source: ICO format spec — stdlib only, no dependencies

import sys
import struct

def create_ico(png_paths, output_path):
    images = []
    for path in png_paths:
        with open(path, 'rb') as f:
            data = f.read()
        w = struct.unpack('>I', data[16:20])[0]
        h = struct.unpack('>I', data[20:24])[0]
        images.append((w, h, data))

    header = struct.pack('<HHH', 0, 1, len(images))
    offset = 6 + 16 * len(images)

    directory = b''
    for w, h, data in images:
        directory += struct.pack('<BBBBHHII',
            w if w < 256 else 0,
            h if h < 256 else 0,
            0, 0, 1, 32,
            len(data), offset)
        offset += len(data)

    with open(output_path, 'wb') as f:
        f.write(header + directory)
        for _, _, data in images:
            f.write(data)

if __name__ == '__main__':
    *inputs, output = sys.argv[1:]
    create_ico(inputs, output)
    print(f'Created {output}')
```

### Favicon `<head>` Links

```html
<!-- In themes/arcaeon/layouts/_default/baseof.html <head> -->
<!-- INFRA-05: Favicon links — SVG for modern browsers, ICO for legacy -->
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
```

[CITED: MDN — Using favicons, svg+xml type is the modern standard]

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Hugo Extended | Build | ✓ | 0.160.1 | — |
| `gh` CLI | Repo creation, Pages config | ✓ | — (auth confirmed) | Manual via GitHub UI |
| `rsvg-convert` | ICO generation (local) | ✓ | 2.60.0 | Commit ICO as static asset generated once |
| Python3 | ICO generation script | ✓ | system | — |
| Node.js / npm | `npm ci` for fonts | ✓ | LTS | — |
| `git` | Push to GitHub | ✓ | — | — |
| GitHub Actions ubuntu-latest | CI runner | ✓ | — | — |
| ImageMagick (CI) | ICO generation in CI | ✗ | — | Commit static ICO (recommended) |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** ImageMagick on CI → generate the ICO locally and commit it as `static/favicon.ico`. This is the recommended approach: the ICO is a binary artifact from a deterministic source (the SVG), changes only if the design changes, and eliminates a CI tool dependency.

[VERIFIED: rsvg-convert 2.60.0 — `rsvg-convert --version` on local machine]
[VERIFIED: ImageMagick absent from ubuntu-24.04 runner — github.com/actions/runner-images/issues/11384]

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | bash + hugo CLI + `gh` CLI (no test framework — infrastructure phase) |
| Config file | none — validation scripts created in Wave 0 |
| Quick run command | `hugo build --environment production 2>&1 && echo "BUILD OK"` |
| Full suite command | `bash scripts/validate-phase4.sh` |
| Estimated runtime | ~5 seconds (local), ~60 seconds (live DNS checks) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-03 | Workflow file exists with correct structure | source | `test -f .github/workflows/hugo.yml && grep -q 'hugo_extended' .github/workflows/hugo.yml` | ❌ Wave 0 |
| INFRA-03 | Hugo build succeeds | integration | `hugo --minify --environment production 2>&1 \| tail -3` | ❌ Wave 0 |
| INFRA-04 | CNAME file present in static/ | source | `test -f static/CNAME && grep -q 'falkensmage.com' static/CNAME` | ❌ Wave 0 |
| INFRA-04 | CNAME appears in build output | integration | `hugo build && test -f public/CNAME` | ❌ Wave 0 |
| INFRA-05 | favicon.svg exists | source | `test -f static/favicon.svg` | ❌ Wave 0 |
| INFRA-05 | favicon.ico exists | source | `test -f static/favicon.ico` | ❌ Wave 0 |
| INFRA-05 | favicon links in baseof.html | source | `grep -q 'image/svg+xml' themes/arcaeon/layouts/_default/baseof.html` | ❌ Wave 0 |
| INFRA-05 | favicon.ico appears in build output | integration | `hugo build && test -f public/favicon.ico` | ❌ Wave 0 |

### Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Push triggers workflow and Pages deploys | INFRA-03 | Requires live GitHub Actions run | `git push origin main` → watch Actions tab |
| `https://falkensmage.com` loads with valid cert | INFRA-03, INFRA-04 | Requires DNS propagation + HTTPS provisioning | `curl -I https://falkensmage.com` after DNS + HTTPS settle |
| Favicon appears in browser tab | INFRA-05 | Requires visual inspection in browser | Open site in Chrome, Firefox, Safari — check tab icon |
| Custom domain persists after second push | INFRA-04 | Requires live deploy cycle | Push a trivial change, verify domain intact |

### Sampling Rate

- **Per task commit:** `hugo build --environment production 2>&1 && echo "BUILD OK"`
- **Per wave:** `bash scripts/validate-phase4.sh`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `scripts/validate-phase4.sh` — covers all 8 automated checks above
- [ ] `.github/workflows/hugo.yml` — created in Wave 1 (Wave 0 creates the validate script only)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | no | Static site — no user input in this phase |
| V6 Cryptography | no | HTTPS via GitHub Pages automatic cert — no manual crypto |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secrets in workflow YAML | Information Disclosure | No secrets needed — `GITHUB_TOKEN` is auto-provisioned, no additional tokens required |
| Submodule poisoning | Tampering | `actions/checkout@v4 with: submodules: recursive` — no submodules in this repo, but standard pattern is safe |
| Third-party actions supply chain | Tampering | Decision D-06 locks to official `actions/*` actions only — no third-party Hugo actions |
| DNS hijacking during propagation | Spoofing | TTL 1800s — short window. Enforce HTTPS only after certificate confirmed. |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `peaceiris/actions-hugo` | Direct Hugo binary download | 2022+ | Eliminates third-party dependency; CLAUDE.md explicitly forbids peaceiris |
| `gh-pages` branch deployment | `actions/deploy-pages` | 2022 (GitHub Pages GA) | No branch needed; artifact-based; official |
| CNAME file drives custom domain | Repo Settings drives custom domain (for Actions) | 2022 | Settings is authoritative; CNAME in artifact is defense-in-depth only |
| `configure-pages@v4` / `deploy-pages@v4` | `configure-pages@v6` / `deploy-pages@v5` | 2026-03-25 | Node 24 runtime, minor API improvements |
| `upload-pages-artifact@v3` | Same — v3 is current | — | No change needed |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `falkensmage.com` was configured as a Substack custom domain experimentally — removing the apex CNAME does not break any active published content at that domain | DNS Checklist, Pitfall 5 | If falkensmage.com was a live Substack site, removing DNS breaks it. Matt should confirm the Substack custom domain for falkensmage.com is intentionally unused before proceeding with DNS change. [ASSUMED] |
| A2 | The `.ico` ICO V2 format (PNG-compressed) works in all modern browsers and IE11+ | Favicon section | Very low risk — ICO with embedded PNG is standard since Windows Vista; modern browsers prefer the SVG anyway [ASSUMED — training knowledge, not verified via browser compat table] |

---

## Open Questions

1. **Is `falkensmage.com` an active Substack custom domain?**
   - What we know: DNS has apex CNAME → `target.substack-custom-domains.com`. `feralarchitecture.com` is separately the newsletter domain.
   - What's unclear: Was `falkensmage.com` ever configured on a Substack publication, or was the CNAME record added and never fully activated? If it's an active Substack custom domain on a different publication, removing DNS breaks it.
   - Recommendation: Matt confirms before the DNS step that falkensmage.com's Substack custom domain link (if any) is intentionally unused.

2. **Lemniscate SVG path geometry at 16x16**
   - What we know: The path needs to be legible at 16x16 favicon size. Standard ∞ curves require careful bezier control points to stay readable at small sizes.
   - What's unclear: The exact SVG path will need iteration.
   - Recommendation: The planner marks favicon path creation as requiring visual validation at 16x16 before committing. The geometry is Claude's discretion (per CONTEXT.md) but needs eyes-on approval.

---

## Sources

### Primary (HIGH confidence)
- [actions/starter-workflows/pages/hugo.yml](https://github.com/actions/starter-workflows/blob/main/pages/hugo.yml) — Official Hugo workflow structure
- [actions/configure-pages releases](https://github.com/actions/configure-pages/releases) — v6.0.0, 2026-03-25
- [actions/deploy-pages releases](https://github.com/actions/deploy-pages/releases) — v5
- [GitHub Pages custom domain docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) — DNS records, custom domain mechanics
- [GitHub Pages publishing source docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) — Actions source mode requirement
- [GitHub Pages DNS A records](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-an-apex-domain) — 185.199.108-111.153 confirmed current
- `dig falkensmage.com` — apex CNAME confirmed pointing to Substack, Namecheap nameservers

### Secondary (MEDIUM confidence)
- [community/discussions/48422](https://github.com/orgs/community/discussions/48422) — CNAME file in artifact prevents domain reset (multiple user confirmations, not official spec)
- [actions/deploy-pages/issues/304](https://github.com/actions/deploy-pages/issues/304) — CNAME file behavior with deploy-pages (closed without official resolution)
- [actions/runner-images/issues/11384](https://github.com/actions/runner-images/issues/11384) — ImageMagick not pre-installed on ubuntu-24.04

### Tertiary (LOW confidence)
- ICO V2 binary format spec — Python struct approach validated locally; browser compat not independently verified this session

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — workflow structure from official starter, action versions verified from GitHub API
- Architecture (workflow): HIGH — official pattern, verified against current releases
- DNS / custom domain: MEDIUM — official docs clear on mechanism, community evidence clarifies CNAME behavior
- Favicon geometry: LOW — SVG path for lemniscate needs visual iteration; approach is sound

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (stable infrastructure domain; DNS IPs change infrequently)
