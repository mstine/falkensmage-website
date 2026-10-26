---
title: "The Notebook Graveyard Was Not a Failure of Will"
subtitle: "Two conditions had to hold for this to work. Until very recently, neither did."
date: "2026-05-20T10:54:03.786Z"
slug: "the-notebook-graveyard-was-not-a"
legacy_url: "https://feralarchitecture.com/p/the-notebook-graveyard-was-not-a"
source: "feral-architecture/2026-05-18-the-notebook-graveyard-was-not-a-failure-of-will.md"
cover: "cover.jpg"
---

Howdy, folks.

I have a graveyard.

Nine personal knowledge management systems are buried in it — 7 Habits and the Franklin Planner; GTD with its inboxes and tickler files; Building a Second Brain with PARA and CODE; Zettelkasten across three different tools; Notion, Logseq, Obsidian (twice — once maximalist, once monastic); Evernote with its eight thousand orphaned notes. Each one started with the dopamine rush of building. Each one filled with hope. Each one quietly turned into a museum exhibit of work I was no longer doing, three to twelve weeks after the build was done.

You know the pattern. You probably have your own version.

The productivity-influencer move at this point is the redemption arc — *then I found the right system and everything changed*, before-and-after photo of a guy who looks like he discovered Notion templates and thanks God every morning that he no longer has to live without them.

That's not the move.

The move is: I had diagnosed the problem. I just couldn't fix it.

By the time I was three or four systems in, I'd figured out the substrate piece. Every PKM book in the genre assumed a brain that could hold its own maintenance load, and my brain — AuDHD-shaped, working-memory-impaired, sustained-attention-impaired, task-initiation-impaired — couldn't. The system wasn't the problem. The substrate maintaining the system was the problem. And the substrate maintaining the system was the same broken thing the system was being built to scaffold. Broken leg, carrying its own cast.

So I tried to build the thing myself.

Twice.

CLI tools. Custom indexers. Shell scripts that crawled my notes and looked for orphans. Wrappers around `obsidian://` URL schemes whose syntax I had to look up every time I sat down. Cron jobs that I'd write, configure, forget existed, then debug six weeks later when they'd been silently failing the whole goddamn time. Filesystem watchers that worked great until I moved a folder. The work I was doing was the same *shape* as what Psyche does for me now. But the abstraction level available to me — file systems, app-protocol URLs, manual indexers, raw scripts — was so low that the development cost of building the prosthetic exhausted the very substrate the prosthetic was being built to scaffold.

I was trying to repair the broken leg with the broken leg.

Both attempts collapsed the same way. Not in a dramatic moment. In a slow attritional drift where the development work outpaced my capacity to sustain it, and the half-built tools became their own graveyard inside the graveyard. I'd ship something brittle, watch it break in a way that required deep focus to fix, sit with the fix for two weeks, lose the thread, find the project six months later with the guilt-and-relief mixture that always meant: *yeah, that fucker's dead too*.

I wasn't waiting for a revelation. I was waiting for tooling I couldn't build.

Two things had to be true for this to work, and until very recently, neither was.

**One:** the substrate doing the maintenance had to be a substrate that doesn't share my biological constraint. Something that holds state coherently, responds to prompts, executes the maintenance work without burning the same cognitive resources I'm trying to scaffold. This was the part I'd figured out years ago and couldn't act on.

**Two:** the abstraction level at which the prosthetic could be *specified* had to be high enough that designing it didn't itself exhaust the substrate. Natural language. Intent expressed in something like the way I already think, executed by something that fills in the implementation work. Not bash scripts. Not URL-scheme syntax I have to look up. Not cron jobs I'll forget. Conversation with a thing that handles the plumbing.

Neither alone was sufficient. A non-biological substrate without a high-enough abstraction level still required me to write the bash. A high-enough abstraction level without a substrate of its own would still have collapsed the maintenance load back onto my addled brain. Both conditions had to land at once. They did. Recently.

The cathedral I'm building now — Psyche, which holds my threads and captures and identity and surfaces what I need when I need it — gets *maintained* by a substrate that doesn't share my biological constraint, and gets *specified* in a register that matches how I actually think. The function that was supposed to live in my brain and didn't, now lives partly in the brain and partly in the agent that sits alongside the brain, described in conversations instead of scripts. Consciousness stays in the brain. The function extends. The implementation disappears.

My brain is the same brain. The clinical profile didn't change. What changed is what carries the maintenance load — and what does the building of what carries the maintenance load.

So the graveyard wasn't a failure of will. It wasn't passivity, either. I'd seen the structural problem and I'd tried to solve it twice with the tools available to me. The tools available to me weren't enough — not because they were bad tools, but because they sat at an abstraction level that required me to use the exact resource the work was trying to compensate for.

The systems weren't bad. They were addressed to a population I am not a member of.

The CLI attempts weren't failures. They were the right diagnosis applied at the wrong abstraction level.

The current cathedral isn't a miracle.

It's two conditions, finally arriving together.

Stay feral, folks.
