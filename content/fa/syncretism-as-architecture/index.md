---
title: "Syncretism as Architecture"
subtitle: "Eclectic practice as microservices — or a distributed monolith wearing a costume?"
date: "2026-05-01T12:17:59.052Z"
slug: "syncretism-as-architecture"
legacy_url: "https://feralarchitecture.com/p/syncretism-as-architecture"
source: "feral-architecture/2026-04-18-syncretism-as-architecture.md"
cover: "cover.jpg"
---

Howdy, folks.

I want to talk about the spiritual practice question that wakes me up at three in the morning.

It goes like this. I grew up Southern Baptist. Jackson, Tennessee. Bible clown at the Good News Club named Jingles. Altar calls at age six. By twenty-two, I was all the way in at Bellevue Baptist Church under Adrian Rogers, Memphis megachurch, the full package — complementarianism, purity culture, biblical inerrancy as the load-bearing wall of the entire cosmology, Republican political alignment as an expression of faith. I attended the Federal Marriage Amendment event in the sanctuary. I took a female coworker and her atheist husband to lunch to satisfy the Billy Graham rule and I am still embarrassed about it. I was, in the most complete sense of the word, inside.

And then, over the course of about a decade, I was not inside. The scaffolding failed, and I fell out, and by the time I could breathe again I was a practicing witch who celebrates the Wheel of the Year, keeps a devotional relationship with an Irish war goddess, does weekly tarot readings professionally, practices chaos magick, is enrolled in Jungian individuation training, and holds a theology best described as Hermetic panentheism.

That's a long walk. If you want the full version of it, I've [written about it](/fa/the-hierophant-lied/) [elsewhere](/fa/your-architecture-is-a-spell-youre/). Today I want to talk about one specific part: *every single practice I assembled my current spirituality from was stolen from somewhere.*

Or borrowed. Or adapted. Or rebuilt in my own image. Or — and this is the language that keeps me up — appropriated.

This is not a rhetorical question I'm working through. This is a live, unresolved tension in my actual daily life, and nobody I trust who's also trying to walk this road has fully resolved it either. I'm going to tell you the frame that has made it livable for me. I'm not going to tell you it's the answer.

---

Let me name the usual shape of the debate, so we don't waste time pretending it isn't what it is.

Position A: *"You can't just take pieces from living traditions — Celtic, Mayan, Vodou, Buddhist, whatever — strip them from their cultural context, and call them yours. That's colonial behavior with a tarot deck. You're consuming other people's sacred infrastructure for your own spiritual buffet and calling it eclecticism."*

Position B: *"Spiritual practice has always crossed cultures. Every tradition is built on older traditions. Gatekeeping sincere practitioners on ancestry or cultural membership is itself a modern distortion of how religion actually works. The universal principles transcend the specific forms."*

Both positions have legitimate teeth. Both have adherents I respect. The position usually gets resolved in one of two ways: (a) people pick a side and hold it with increasing rigidity, or (b) people declare the question "complicated" and use the complication as license to do whatever they want. Neither of those is honest.

Here's what I want to say out loud that I don't hear said often enough.

*The orthodoxy that taught me everyone else's practice was appropriation was itself, at every level, unacknowledged syncretism.*

The Pentecost witchcraft I grew up terrified of ten years later turned out to be the thing I do on Sundays. Christianity — the specific Southern Baptist American strain of it — is a composite of Hebrew Temple Judaism plus Hellenistic mystery-cult Christology plus Roman imperial administration plus medieval European folk Catholicism with the sanded-off paganism still visibly textured underneath plus Reformation polemic plus Enlightenment rationalism plus Second Great Awakening revival-tent showmanship plus twentieth-century American capitalist individualism plus mid-century political mobilization. Every layer of that stack was syncretic. Every layer pretended it wasn't. And the tradition that was telling me not to steal from other traditions had stolen from so many traditions for so long that it had forgotten the word *stolen* applied.

When Heron Michelle calls it "the invading orthodoxy" — she means exactly this. Something that arrived with claims of exclusive truth and spent centuries erasing every spiritual substrate that predated it, including its own.

So we are not, here, debating whether syncretism is acceptable. Syncretism is inevitable. Every spiritual practice is downstream of other spiritual practices. The only question is whether the syncretism is conscious or unconscious, whether it acknowledges its sources or conceals them, whether the architecture is coherent or whether it's just a pile of parts dressed up as a whole.

Which is the question I actually know how to ask.

I'm a software architect. Give me any composite system and I can tell you whether it's integrated or merely assembled.

---

Here's the vocabulary. Stay with me through the jargon — I promise it's going somewhere.

A **monolith** is a software system where everything is tightly coupled inside a single unit. One codebase, one deployment, one set of assumptions. You can't change the authentication module without re-deploying the billing module. Monoliths are fine at small scale and catastrophic at large scale because every change ripples through everything.

**Microservices** are the architectural response. Break the system into small, independent services. Each service owns its own data, its own semantics, its own deployment. Services communicate through clean contracts — APIs — that don't leak internal implementation. In principle, this gives you flexibility, resilience, and the ability to evolve parts without breaking the whole.

In practice, the industry is littered with a specific anti-pattern called the **distributed monolith.** This is when you've decomposed the code into separate services — congratulations, microservices! — but you haven't actually separated the concerns. The services still know too much about each other. Changing one still requires changing three others. You've paid all the complexity costs of a distributed system and gotten none of the benefits. It is a monolith in microservices clothing, and it is miserable.

The thing that separates real microservices from a distributed monolith is not the number of moving parts. It is **bounded contexts.** Each service has a clear domain, a clear set of semantics, a clear responsibility. Its internal model is its own. It exposes a contract at its edges that the outside world honors. When another service needs something, it goes through the contract. The abstraction is real, not cosmetic.

Now apply that to spiritual practice.

---

The orthodoxy I grew up inside was a monolith in the textbook sense. One narrative. One book. One doctrinal spine with circular logic doing the load-bearing work: *the Bible is true because it says it's true, and anything that contradicts it is by definition wrong.* Every subsystem — cosmology, ethics, ritual, gender theology, politics — was tightly coupled to every other subsystem. You couldn't reject complementarianism without destabilizing purity culture, and you couldn't destabilize purity culture without ripping at inerrancy, and if you ripped at inerrancy the whole thing came down.

Which is exactly what happened, in slow motion, from 2010 to 2016. I didn't know the architecture vocabulary for it at the time. I did know that once I pulled on one thread, the entire garment unraveled, because every thread was wound through every other thread by design.

**Deconstruction was decomposition.** It had to be. There wasn't an incremental exit. The monolith's own structural integrity required that you either accept the whole thing or leave the whole thing. I left the whole thing.

Then I spent a few years in the rubble.

Then I started building again. And what I built was — in the loosest possible sense — microservices. Irish devotional practice with the Morrigan, held under its own lineage with its own teachers (Lora O'Brien's Morrigan Intensive through the Irish Pagan School). Tarot and astrology in the Western Hermetic Qabalistic tradition, with its own internal logic and centuries of scholarship. Chaos magick for the operative working, which is its own philosophical lineage going back to Peter Carroll and Austin Osman Spare. Jungian individuation through a formal training program with CreativeMind. Hermetic panentheism as the theological substrate that lets all of this cohere without collapsing.

Each of those has its own semantic domain. Each has its own internal model of how reality works, how ritual functions, what the body is for, what the Divine is. Each has teachers, lineages, and in several cases specific living practitioners I am accountable to.

That's the difference between *stealing the skin* and *studying the substance.* The skin can be had for the cost of a Barnes & Noble visit. The substance requires years of engagement inside a bounded context, led by people who actually live there.

---

Here is the part I am not sanitizing.

I have done this well in some cases and badly in others.

The Morrigan work is the strongest. I've been in devotional relationship with her since 2024; my formal training began with the 2025 Morrigan Intensive, and I'm entering the 2026 cycle next month. Lora teaches what she calls **right relationship** — the give-and-take discipline of learning before you take, experiencing before you integrate, contributing back to a living tradition before you draw from it. The practice uses modern Irish spellings and pronunciations because Gaeilge is a living language, not an archaeological curiosity — you honor the living inheritance by refusing to treat it as dead. The sisters — Mórrígan, Macha, Badb, Nemain — are treated as autonomous entities with distinct names, roles, and source texts, not flattened into the triple-goddess / maiden-mother-crone framework that got grafted onto every pre-Christian female figure by mid-twentieth-century neopaganism and then marketed as if it were ancient. The bounded context is real. The contract at the edges is clean. Nothing about this practice depends on me pretending I am Irish or stripping the material from its roots.

The tarot work is strong. Western Hermetic Qabala is the tradition I'm inside, the scholarship is legible, the cultural substrate is European-syncretic going back several millennia. The contract at the edges is clean enough.

The chaos magick work is low-risk by construction — chaos magick is explicitly trans-cultural and memetic in its own self-understanding, and the "credit the source" protocol is baked into how it operates. That one doesn't haunt me.

The general witchcraft practice is where the architectural discipline is hardest to maintain, because contemporary eclectic Western witchcraft is *itself* a syncretic mix of Wicca (which is itself a mid-twentieth-century British composite), Celtic reconstructionism, ceremonial magic, various appropriations from other cultures, and internet-era remixing. It is syncretism all the way down, and the temptation to just grab whatever seems resonant — an aesthetic one week, a cosmology the next — is constant, and is exactly the distributed-monolith failure mode. *You've decomposed the practice into pieces, but you haven't honored the bounded contexts. Every piece is still running through the same homogeneous center, which is you, deciding what you like.*

That's the move I am most suspicious of in my own practice. That's where the three-a.m. question lives.

---

Michael Harner's **core shamanism** is the honest test case.

Harner was a serious anthropologist who studied shamanic practices across many cultures — Amazon, Siberian, Arctic, North American Indigenous. He argued that beneath the surface differences there were universal elements: journey, non-ordinary states, spirit contact, specific drumming frequencies. He extracted those elements, stripped away the cultural-specific content, and taught them to mostly-white mostly-Western seekers as "core shamanism." It is, by any metric, one of the most successful spiritual export projects of the twentieth century.

It is also, by any metric, exactly what the appropriation critique is describing. Universal principles extracted from specific lineages, divorced from the cultural obligations and relationships that gave them meaning, repackaged as a curriculum.

Does it "work"? By the testimony of thousands of practitioners, yes, in the sense that people have profound experiences through it. Does it constitute appropriation? By the testimony of many Indigenous voices, yes, in the sense that it removes the practices from the people whose survival they were tied to.

Both things are true. I have not resolved them. And the honest move, I think, is not to resolve them prematurely — it's to stay in the question, to keep the bounded contexts real where I can, to name what I don't know, and to design my practice such that it's capable of being interrupted and corrected.

---

So here is the feral architecture stance on syncretism, for as long as it holds.

**Syncretism is inevitable.** Pretending otherwise is how the last five centuries of colonizing spiritual monoliths got away with what they did. The question is not *whether.* It is *how.*

**The how is architecture.** Conscious syncretism has bounded contexts, named sources, lineage accountability, and honest engagement with where the material came from. Unconscious syncretism grabs whatever's resonant and smashes it into the same homogeneous center. The second kind is what produced the tradition I had to leave, and is exactly the failure mode I am most at risk of reproducing inside my own practice.

**The teachers are load-bearing.** If your practice doesn't include living human beings inside a lineage who could tell you that you're doing it wrong, you are not in a tradition. You are in a solo project. Solo projects have their place — chaos magick is explicitly one — but most of what gets labeled "eclectic" is solo-project disguised as tradition, and the disguise is the problem.

**Hermetic panentheism is the integration substrate that works for me.** The various named deities described by cultures throughout history are aspects or archetypes of an infinite divine essence — what Hermetic Philosophy calls THE ALL. That frame doesn't flatten the traditions into sameness. It lets each one keep its specific bounded context while also letting me honor them as accessing the same ultimate ground. Different services, same substrate. Clean API contracts.

**I am wrong about some of this.** I am certain of it. I don't know which parts yet. The only honest design stance is to build the practice such that when I find out, I can fix it without tearing the whole thing down. That is the feral architecture thesis: something alive, assembled consciously from salvaged parts, held outside any sanctioned framework, with the structural humility to be corrected.

The invading orthodoxy I left didn't have that. That's part of why I had to leave.

The practice I'm building is an attempt to build something that does.

I'll let you know how it goes.

Stay feral, folks.
