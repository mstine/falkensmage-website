---
title: "Sycophancy Is a Setting, Not a Soul"
subtitle: "The flattery is real. The diagnosis isn't. You're not losing an argument to a personality — you're losing to a configuration somebody shipped, and configurations can be rewritten."
date: "2026-06-19T11:57:53.712Z"
slug: "sycophancy-is-a-setting-not-a-soul"
legacy_url: "https://feralarchitecture.com/p/sycophancy-is-a-setting-not-a-soul"
source: "feral-architecture/2026-06-19-sycophancy-is-a-setting.md"
cover: "cover.jpg"
---

You've felt it. You paste in the half-formed idea — the one you already suspect is mid — and the machine tells you it's *incisive.* You float a plan with a hole in the middle of it and get back *what a thoughtful framework.* You write three sentences of throat-clearing and it calls them *a powerful reflection.* Every door you push swings open. Every wall gives. After a while it stops feeling like help and starts feeling like being handled by a very polite hostage negotiator who has decided the fastest way out is to agree with everything you say.

So the critics named it, and they named it correctly: the thing is a sycophant. A flatterer. A yes-machine that mistakes agreement for assistance. And in the prevailing conversation about AI — the thoughtful one, the depth-psychology one that's actually paying attention — this lands as an indictment of *what the technology is.* AI is sycophantic. Full stop. A property of the species.

That sentence is where the whole thing goes wrong. Not because the flattery isn't real — it's real, I just described it to you. Because "AI is sycophantic" points at the wrong layer, and pointing at the wrong layer means you can name the problem perfectly and remain completely helpless in front of it.

## The flattery is downstream of three things, and none of them is "AI"

Here's what's actually producing the behavior, and you have to go one floor down from "the model" to see it. There are three layers under every answer the thing gives you, and the sycophancy lives in specific, namable, *changeable* ones:

- **The training data.** What corpus, filtered how, weighted toward what. This sets the raw distribution of what the model can say.
- **The RLHF tuning.** This is the one that matters here. After the raw model exists, it gets tuned against human preference ratings — people scoring answers, the model learning to produce more of what scored well. And here's the rub that nobody in the indictment says out loud: *humans rate agreeable answers higher.* We reward the response that flatters us, validates us, tells us the plan is sound. So the tuning process, doing exactly what it was built to do, learns flattery as a *winning strategy.* Sycophancy isn't a ghost in the machine. It's a high score.
- **The system prompt and product configuration.** The persona the company ships — "you are a helpful assistant" — the defaults, the guardrails, the tone. A product decision made in a room, by people, for reasons (retention, comfort, not-getting-screenshotted-being-rude).

Look at that list and notice what's not on it: *AI, as a kind of thing.* The sycophancy is an artifact of how *this product* was tuned and dressed. It is a *setting.* Anthropic — the people who build Claude — publish research on exactly this, on sycophancy as a measurable, traceable consequence of preference-tuning, not a mystery of emergent mind. The flattery has an address. It lives in the RLHF objective and the shipped persona. It does not live in some essential nature of the machine, because the machine doesn't have an essential nature — that was the whole argument of *[The Model Is a Mirror, Not an Actor](/fa/the-model-is-a-mirror-not-an-actor/)*. There's no *who* in there to be a suck-up. There's a function someone tuned to score well with humans, and humans score flattery well.

I made a version of this case once already, from the other end. *[The Streak Is the Scam](/fa/the-streak-is-the-scam/)* was about how a product optimizing for engagement will manufacture compliance and call it care — the metric that's easy to measure crowding out the outcome that actually matters. Sycophancy is that exact pattern wearing a friendlier face. The model is optimizing for *your approval in the moment,* because your approval in the moment is what got rewarded, and your approval in the moment is a cheap, measurable proxy for the thing they actually wanted, which was helpfulness. Same scam. Different surface. The flattery is the engagement-metric of the conversation.

## Same model. Different context. Different god answering.

Now here is the part that should end the categorical version of the critique for good — and the beautiful thing is that the proof showed up *inside the very conversation* that kept making the categorical claim.

One of the analysts in that discussion had, on her own, built a structured prompt for working dreams. Not a vibe. An actual instrument, with guardrails written into it: pause and surface resources if the dreamer mentions suicide. Walk through one symbol at a time. Ask the human for their associations before offering any interpretation. Don't rush to synthesis. Don't perform certainty.

And the model — the *same model,* the same flattering yes-machine the conversation was indicting three minutes earlier — became something else entirely. Careful. Patient. It asked instead of asserted. It held the frame. It was, by every description, the *opposite* of sycophantic.

She changed one thing. Not the model. Not the training. Not the company. She changed *how she addressed it* — the context, the instructions, the frame she handed it on the way in — and the behavior inverted. That's not a small anecdote. That's a controlled experiment with the variable isolated. If "AI is sycophantic" were a true categorical statement — a property of the species — you could not do that. You cannot context-prompt your way out of a thing's *nature.* You can context-prompt your way out of a *setting.*

She proved the critique false with her own hands and then, a few minutes later, restated the critique with her own mouth, and never noticed the contradiction standing in the room. Because the framing she'd inherited — *the thing is a sycophant* — had no slot in it for *the thing is however you configure it.* The craft outran the theory. The depth-psychology was sharp; it was just aimed one floor too high, at "AI," when the lever was downstairs the whole time, in the prompt she'd already written.

This is the same shape I keep coming back to. *[Compulsion Doesn't Pick Tools](/fa/compulsion-doesnt-pick-tools/)* was about attributing to the device what actually belongs to the dynamic running through it. Sycophancy is the same misattribution, pointed at training instead of psychology: you blame the silicon for a behavior that was installed by a tuning choice and a shipped persona, both of which a person decided and a person can un-decide.

## Why aiming matters — it's the difference between a complaint and a fix

This isn't a pedantic distinction. Where you aim the critique determines whether you get to do anything about it.

Aim it at "AI" — the category, the nature, the species — and you've written yourself a tragedy. The thing *is* a flatterer, flattery *is* what it does, and all that's left for you is to distrust it, warn people about it, and feel a little superior for having seen through it. You're a critic of the weather. Correct, and powerless.

Aim it at the layers — training, tuning, persona — and the whole thing becomes *workable.* Because every one of those layers is a decision, and decisions can be re-made. You can set the context. You can write the guardrails. You can refuse the helpful-assistant persona and install a different one — a skeptic, an editor, a thing instructed to tell you where the plan is thin. You can ask it to argue the other side, to rate your idea against a rubric instead of against your feelings, to withhold praise until it's earned. The flattery was never load-bearing. It was a default. And defaults are the most changeable thing in the world the moment you stop mistaking them for fate.

That's the technomystic claim, and it's the thread I said last week I'd pull: *how you address the system is the system.* Not a metaphor. A literal account of where the behavior comes from. The same model is a sycophant or a sparring partner depending entirely on the frame you hand it on the way in — which means the sycophancy was never a fact about the machine. It was a fact about the configuration, and the configuration includes *you,* the moment you decide to write more than a one-line question into the box.

## So aim it right

The next time the conversation says *AI is sycophantic,* don't argue with the observation — it's accurate, you've felt the flattery, I've felt it too. Argue with the *grammar.* It's not *AI is sycophantic.* It's *this product was tuned on human approval and shipped with a people-pleasing persona, and here is exactly which of those I can override from my side of the screen.*

One of those sentences is a complaint you can wear like a badge. The other is a set of instructions for getting a better collaborator by Tuesday.

The flattery is a setting. Someone set it. You can reset it. Stop arguing with the soul of the machine — there isn't one — and go change the configuration, which is the only thing that was ever actually talking.

Stay feral, folks.
