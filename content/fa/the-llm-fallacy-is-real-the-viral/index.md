---
title: "The LLM Fallacy Is Real. The Viral Version Isn't."
subtitle: "What Kim, Yu, and Yi actually wrote — and what Baldur Bjarnason actually argued."
date: "2026-04-28T14:35:20.244Z"
slug: "the-llm-fallacy-is-real-the-viral"
legacy_url: "https://feralarchitecture.com/p/the-llm-fallacy-is-real-the-viral"
source: "feral-architecture/2026-04-23-llm-fallacy-viral-version.md"
cover: "cover.jpg"
---

Howdy, folks.

A post has been making rounds this week. You've probably seen it. It cites an actual arxiv paper introducing the "LLM fallacy" as an AI-induced Dunning-Kruger effect — people mistaking AI-assisted work for evidence of their own standalone competence. So far, so defensible. Then the post pivots. LLMs are "architected like a con man." Users are being "inculcated into a cult." CEOs — who, we're told, "tend not to be the brightest" — are about to walk capitalism off a cliff.

I pulled the paper. I also went back to Baldur Bjarnason, whose LLMentalist essay keeps getting name-checked in this kind of post and whose two books I've actually read. And what I found is that the cult-epidemic-capitalism-collapse frame is not the argument the paper makes, not the argument Baldur makes in his actual book, and — ironically — is the exact failure mode Baldur himself named and warned about.

Let's do the work.

## What Kim, Yu, and Yi actually wrote

The paper is Hyunwoo Kim, Harin Yu, and Hanau Yi, arxiv 2604.14807, April 2026. It's a conceptual framework paper. Not an empirical study. The authors say this explicitly in Section 6 — "these observations are intended as conceptual and cross-contextual patterns rather than as controlled empirical validation." There is no n. There are no effect sizes. There is no study showing a specific percentage of users experience the fallacy at a specific rate under specific conditions.

What they did write: a careful definition (yes, people do misattribute AI-assisted work as their own standalone capability), a four-part mechanism (attribution ambiguity, fluency illusion, cognitive outsourcing, pipeline opacity), a six-domain typology, and a serious call for literacy interventions and process-aware evaluation frameworks. Not abstinence. Literacy.

And here is the part the viral post skipped entirely. Section 8 is the authors' own methodology disclosure. They wrote the paper using — their words — "a human-in-the-loop, human-in-control, and human-as-final-author model of collaboration," governed by a structured prompting framework called NLD-P. They used an LLM to produce the paper about the LLM fallacy, under a disciplined architecture, and were transparent about it.

Their own practice is the answer to the fallacy they're describing.

## The Baldur move

Which brings me to Baldur Bjarnason, whose work I respect. I've read both editions of *The Intelligence Illusion*. I've read the LLMentalist letter. The man has done the reading. He is not a lazy critic. And he has put a concept to work in his writing that I think is one of the most useful pieces of vocabulary anyone's brought to AI discourse.

He calls it criti-hype.

Criti-hype is when critics amplify vendor marketing by assuming the products work as claimed and then extrapolating dystopian scenarios from that marketing fantasy. Rather than examining what the systems actually do, criti-hype takes the hype at face value and builds the cataclysm on top of it. Criti-hype, Baldur points out, shifts the debate toward hypothetical superintelligence and mind-warping con artistry rather than documented harms occurring today.

Read that again. Now go back and read the viral LinkedIn post. It assumes LLMs have the seductive, irresistible, mind-warping psychological power the marketing implies. It extrapolates a cult-scale mental health epidemic, mass layoffs, capitalism collapsing into rubble. It bypasses any discipline-level question about how disciplined users actually relate to these systems.

The post is criti-hype by Baldur's own definition. It invokes the man while doing the exact thing he spent a chapter warning against. That's not engagement. That's cosplay.

## Engaging the real argument — the bumblebees

The strongest version of Baldur's case isn't in the LLMentalist essay. It's in the bird-brains chapter. Bumblebees have about 500,000 neurons. They solve novel puzzles, teach each other solutions, and demonstrate adaptive problem-solving that would require a human designer if you tried to engineer it from scratch. GPT-4 is estimated at roughly a trillion parameters — about a million times more complex than a bumblebee's nervous system. And Baldur's observation is that the bumblebee is still better at genuine adaptive reasoning in unfamiliar terrain.

His conclusion is philosophical: reasoning in biological minds is an inherent property of an embodied, chemically-mediated, constantly-updating system. It's not an emergent property of pattern-matching at scale. The LLM, he writes, is "water running down pathways etched into the ground over centuries by the rivers of human culture." It is downstream of the thinking that made the training data. It is not the thinking.

That's a real philosophical claim and it deserves a real response.

## Where I think Baldur is wrong now

Two places.

First: his strongest fragility examples — "breaks as soon as you rephrase" — were truer in 2023 than they are in 2026. Reasoning-model architectures, extended-thinking systems, self-critique loops, and tool use have narrowed the fragility envelope measurably. The static-snapshot model he describes is a fair description of GPT-3.5 on a blank prompt. It's a thinner description of what happens when you build a system around the model.

Second — and this is the one that matters: his frame treats all users as undifferentiated marks. He writes, compassionately, that "falling for this statistical illusion is easy" and that it "has nothing to do with your intelligence." I appreciate the generosity. I also think it collapses the variable that matters most: discernment.

The user who treats the LLM as an oracle will experience the fallacy. The user who treats it as an interlocutor — who pressure-tests, corrects, overrides, rejects outputs that drift from their voice or values — is running a different process entirely. Baldur has no model of that user. Baldur's mark is passive. The disciplined user is not passive.

## Where Baldur is right and I should say so

He's right that the industry's evidentiary standards are weak. He's right that RLHF can't directly reward factuality and that its raters are largely low-wage workers without domain expertise. He's right that anthropomorphism supercharges automation bias — this is actually load-bearing for the Kim/Yu/Yi paper too. He's right about the mediocrity trap: unscaffolded LLM output regresses toward the median of training data. He's right that "use for modification, not wholesale generation" is genuinely good operational practice. He's right that the C-suite AI adoption wave looks more like a cultural cascade than a considered strategic decision.

And he's right about criti-hype, which is why it's so absurd to watch the viral frame do criti-hype at him.

## The remediation is already in the paper

Kim, Yu, and Yi spell it out in Sections 7 and 9. Interface designs that make system contributions explicit. Educational approaches that improve AI literacy. Process-aware evaluation frameworks that distinguish between system-assisted performance and independently grounded competence. Metacognitive awareness training.

None of it says "stop using LLMs." All of it says the same thing from different angles: build the discipline, build the architecture, build the evaluation process that can tell assisted work from unassisted work. The fallacy isn't produced by the tool. It's produced by the absence of a process-aware frame around the tool.

I've spent the past month building exactly that. It's called Psyche. It holds me to a contract the model can't flatten me out of. The site explains it better than an inventory here would: [psyche.sh](https://psyche.sh).

What I will say inline is this: the feedback loop is load-bearing. Every correction I log accumulates. The model doesn't drift me toward a sycophantic echo, because the architecture won't let it. That's not superpowers. That's discipline dressed up as infrastructure.

## The actual call

The LLM fallacy is real. The attribution error the paper names is a genuine phenomenon that genuinely affects people. The machine is not the problem. The discipline is the answer. The remediation is already specified — by the paper itself. The work is unglamorous: literacy, process-aware evaluation, explicit boundaries between assisted and independent work, and a usage pattern that treats the tool as an interlocutor rather than an oracle.

The cult isn't forming around LLMs. The cult isn't forming around disciplined users either. What's forming is a discourse where criti-hype on one side amplifies marketing hype on the other, both groups are convinced they're the clear-eyed ones, and the quiet work of actually using the tool well goes uncredited and unseen.

Do the quiet work. Read the paper before you quote it. Read the books of the people you're name-checking. Argue with what the machine says. Correct it when it drifts. Hold it to a contract.

That's not cult hygiene. That's just hygiene.

Stay feral, folks.
