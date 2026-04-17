# Phase 4: Production Deploy - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 04-production-deploy
**Areas discussed:** Favicon design, Workflow triggers, Domain + repo setup

---

## Favicon Design

| Option | Description | Selected |
|--------|-------------|----------|
| ARCAEON glow mark | Electric Violet lemniscate on transparent background, subtle Neon Magenta outer glow. Clean geometric curves, reads well at 16x16 and 32x32. | ✓ |
| Solar White on Void Purple | White/warm lemniscate on dark filled square. Higher contrast, less glow aesthetic. | |
| Minimal monochrome | Simple white lemniscate, no background, no glow. Clean and universal. | |

**User's choice:** ARCAEON glow mark
**Notes:** Consistent with site's dark graphic novel aesthetic. Glow treatment matches the brand.

### Follow-up: Favicon Source

| Option | Description | Selected |
|--------|-------------|----------|
| Committed SVG file | Hand-craft SVG, commit to static/. Simple, version-controlled. | |
| Hugo-generated at build | Template-generate SVG during Hugo build. Favicon inherits palette changes automatically. | ✓ |

**User's choice:** Hugo-generated at build
**Notes:** Keeps favicon in sync with palette tokens from hugo.toml.

---

## Workflow Triggers

| Option | Description | Selected |
|--------|-------------|----------|
| Push to main only | Simple: every push to main builds and deploys. No PR builds. Solo project. | ✓ |
| Push to main + PR checks | Build on PRs too to catch failures before merge. More CI discipline. | |
| Manual dispatch only | Only deploy when manually triggered. Maximum control, zero automation. | |

**User's choice:** Push to main only
**Notes:** Solo committer, PR previews add complexity for zero value.

---

## Domain + Repo Setup

### Repo Creation

| Option | Description | Selected |
|--------|-------------|----------|
| Create repo in this phase | Use `gh repo create`, set up remote, push. Everything automated. | ✓ |
| Repo exists, just needs remote | Already created on GitHub, just add remote and push. | |
| I'll create it manually | Handle repo creation manually. Phase only covers workflow, CNAME, favicon. | |

**User's choice:** Create repo in this phase
**Notes:** Full automation — repo creation through deployment in one shot.

### Repo Visibility

| Option | Description | Selected |
|--------|-------------|----------|
| Public under personal account | GitHub Pages free tier. Simplest path. | ✓ |
| Public under an org | Under a GitHub org (RitualSync, etc.). | |
| Private repo | Requires paid plan for Pages. More locked down. | |

**User's choice:** Public under personal account
**Notes:** Free hosting, no paid plan needed.

### DNS Approach

| Option | Description | Selected |
|--------|-------------|----------|
| CNAME file + DNS checklist | Create static/CNAME and include step-by-step DNS pointing checklist. | ✓ |
| CNAME file only | Just the file. User handles DNS independently. | |

**User's choice:** CNAME file + DNS checklist
**Notes:** Documented steps for pointing falkensmage.com to GitHub Pages.

---

## Claude's Discretion

- SVG lemniscate curve geometry and glow filter parameters
- Exact workflow YAML structure within pattern constraints
- `.ico` generation approach
- DNS checklist formatting

## Deferred Ideas

None — discussion stayed within phase scope
