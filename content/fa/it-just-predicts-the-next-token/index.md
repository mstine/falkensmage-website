---
title: "It Just Predicts the Next Token"
subtitle: "And so do you."
date: "2026-04-23T15:45:46.403Z"
slug: "it-just-predicts-the-next-token"
legacy_url: "https://feralarchitecture.com/p/it-just-predicts-the-next-token"
source: "feral-architecture/2026-04-22-it-just-predicts-the-next-token.md"
cover: "cover.jpg"
---

Howdy, folks. It's Wednesday morning and I've already seen the phrase three fucking times before breakfast. LinkedIn. Threads. A thoughtful Substack piece from someone I otherwise respect. Six words, arranged with the confidence of a closing argument:

*It just predicts the next token.*

People say it and stop talking. As if the sentence has performed the refutation. As if anyone still paying attention will now nod solemnly and agree that the robot is, indeed, not impressive.

I've been sitting with that phrase for two years. Not because I think it's wrong — it is, at one level of description, true. It's because it's doing something very specific, and the thing it's doing is the single most interesting part of it.

Here is the part I wish I could skip. A year ago, I was saying it myself.

I remember the moment because I'm flying back to it tomorrow. Last CreativeMind summit. Debra and Dr. Rob on stage, leading open discussion with the whole cohort about AI — what it was, what it wasn't, what any of us were supposed to do with it. I offered the room the six-word dismissal. I said it with the confidence of a closing argument. I felt the familiar pleasure — the pleasure of having seen through the trick while everyone else was still falling for it. The room absorbed it. We moved on.

Tomorrow I'll be in the same room (different city), and I will not be saying it. I want to tell you what changed.

Let me show you.

## The truism at the bottom

The phrase isn't a lie. Transformer LLMs are trained on a next-token objective. You show the model a ton of text, and at each position you ask it to predict what comes next. It guesses, you compute how wrong it was, you adjust the weights a tiny fraction toward the right answer, repeat approximately seven trillion times, and what you get on the other end is a system that is very, very good at predicting what comes next in a long stretch of text.

This is not controversial. This is how the things are built. When someone on Threads announces that GPT-4 "just predicts the next token," they are, at the level of the training objective, saying something technically correct.

They're also saying something that stopped describing what these systems actually fucking *do* about four years ago.

Here's the thing about a training objective: it's the pressure that shapes the system, not the system itself. You train a dog with food rewards. You can call the dog "just a food-reward-maximizer" and, at the level of the training procedure, you'd be right. You'd also be missing everything that matters about what happened while the food rewards were being applied. The dog, it turns out, learned its way around your house. It learned your moods. It learned to recognize the sound of your car from three blocks away. None of that was directly in the food reward. It emerged because predicting which behavior would be rewarded required modeling an entire social environment.

Saying an LLM "just predicts tokens" is like saying an operating system "just processes logic gates." Technically true at one level of description. Immediately leaky as a description of what the thing does.

OK. So the dismissers' phrase gestures at a truism that became trivial about the same time the field started building the things. If we're going to take the dismissal seriously, we have to ask what else it's claiming. And there are two things it's implicitly claiming. Both of them fail.

## Pressure one: the engineering stack

The first failure is empirical. The closed-world autocomplete picture — a base model doing a single forward pass over a prompt and emitting the next token — hasn't described frontier systems since roughly 2022.

Here's what's been stacked on top.

**Chain of thought**[^1] showed that prompting a large enough model with worked reasoning traces made math and symbolic-reasoning accuracy jump non-linearly. A follow-up paper[^2] demonstrated that a single canned phrase — *let's think step by step* — took InstructGPT's MultiArith accuracy from 17.7% to 78.7%. A magic fucking phrase. The capability was latent in the weights; the phrase unlocked it. What is conceptually uncomfortable about this: each reasoning token the model generates becomes context for the next forward pass. The model is using its own output as a scratchpad. It is allocating *serial computation* to a single problem. That is not the shape of autocomplete.

**Self-consistency**[^3] samples a bunch of different reasoning chains and takes the majority vote. **Tree of Thoughts**[^4] runs the model as both generator and evaluator, doing breadth-first and depth-first search over reasoning paths. On the Game of 24, GPT-4 with plain chain-of-thought solved 4%. The same weights under Tree of Thoughts solved 74%. Same model. Different scaffolding. A 17× performance gain from changing the control flow around the forward pass. **Reflexion**[^5] has the agent write a natural-language post-mortem of each failure, store it in episodic memory, and retry — learning across trials without a single gradient update.

Then came the reasoning models. OpenAI's o1 in September 2024 and o3 in December 2024 trained a hidden chain of thought with outcome-based reinforcement learning. o1 took AIME 2024 from GPT-4o's 12% to 74% single-sample and 93% with re-ranking. o3 hit 87.5% on ARC-AGI-1 at the high-compute tier. DeepSeek-R1 in January 2025 demonstrated the phenomenon with pure reinforcement learning on a base model — no supervised fine-tuning — and reported a now-famous intermediate checkpoint where the model spontaneously produced the lines:

> *Wait, wait. Wait. That's an aha moment I can flag here. Let's reevaluate this step-by-step…*

The authors called it *"a captivating example of how reinforcement learning can lead to unexpected and sophisticated outcomes."* I'd call it something else, but we'll get there.

Meanwhile the systems grew arms and eyes. OpenAI shipped function calling in June 2023. Toolformer[^6] taught a model to decide, on its own, which APIs to call. ReAct[^7] interleaved Thought → Action → Observation loops, grounding reasoning in live external information. By October 2024 Anthropic shipped computer use — a model taking screenshots, reasoning about UI elements, and emitting mouse and keyboard actions. Model Context Protocol landed in November 2024 and within three months had over a thousand community servers; OpenAI and Google adopted it in March 2025; Anthropic donated it to the Linux Foundation in December. LLMs are no longer standalone text processors. They are nodes in a protocol graph.

Multimodality changed what "predicting" even means. GPT-4o was trained natively on interleaved text, vision, and audio tokens with roughly 320ms voice latency. Gemini was, in its designers' phrase, *built from the ground up to be multimodal* — a single autoregressive transformer modeling *p*(text, pixels, sound) jointly. When the vocabulary being predicted spans sight, sound, and action, "just predicting tokens" stops meaning what the critique implies.

Add retrieval-augmented generation, 200K-to-2M-token context windows, persistent memory that references all prior chats, OS-inspired paging between main context and archival storage. What you have is a composite cognitive system with working memory, long-term memory, effectors, and sensors.

And if you still think it's autocomplete, I have a dog I'd like to sell you as a simple food-reward-maximizer.

## Pressure two: brains

This is where the dismissal gets philosophically awkward.

The leading scientific theory of biological cognition for the last two decades is predictive processing. The lineage runs Helmholtz (1867, "unconscious inference") → Gregory ("perceptions are hypotheses") → Hinton and Dayan's Helmholtz machines → Rao and Ballard's predictive coding in V1 → Karl Friston's free-energy principle → Andy Clark, Anil Seth, and Jakob Hohwy.

The claim is this: brains are prediction machines. Perception is not a passive reception of sensory data. It is the brain's continuous effort to *predict* what sensory data will arrive, with the actual incoming data serving as a correction signal against the prediction. When you "see" something, what you're experiencing is not the photons hitting your retina. You're experiencing your brain's best guess about what is out there causing those photons. When the guess matches the data, you have stable perception. When the guess fails badly enough, you have hallucination.

Karl Friston, in his canonical 2010 paper[^8]:

> *Any self-organizing system that is at equilibrium with its environment must minimize its free energy… Biological agents must therefore minimize the long-term average of surprise.*

Prediction is not what brains happen to do. It is the signature of being a bounded system at all.

Andy Clark, in 2013[^9]: *"Brains are essentially prediction machines… a hierarchical generative model that aims to minimize prediction error within a bidirectional cascade of cortical processing."* In *Surfing Uncertainty* (2016): *"Minds like ours are prediction machines — devices that have evolved to anticipate the incoming streams of sensory stimulation before they arrive."*

Anil Seth, in *Being You* (2021): *"The world we experience comes as much from the inside out as the outside in… Perceptual content is nothing more and nothing less than our brain's best guess of the hidden causes of its colourless, shapeless, and soundless sensory inputs."* And: *"The self is another perception, another controlled hallucination, though of a very special kind."*

So let me be clear about what is being said when someone says LLMs "just predict the next token." They are using the word *prediction* as if it were damning. As if prediction were a lesser form of cognition, a cheap mimicry of the real thing. They are doing this in 2026, with two decades of mainstream cognitive-science research on the desk, saying that *prediction is the real thing*.

The world you see is predicted. The red is not in the photon. The sound is not in the air. *You* are a Bayesian best guess your brain makes about what kind of thing is making these predictions. You are a controlled hallucination running on meat.

The rhetorical force of "mere prediction" depends on the listener not realizing that the same phrase names the dominant unifying principle in contemporary theoretical neuroscience.

That's not a gotcha. That's the hinge.

There is direct empirical convergence, too. A 2022 *Nature Neuroscience* study[^10] found that during natural listening, human brains and autoregressive LLMs share three computational signatures: pre-onset next-word prediction, post-onset prediction-error surprise, and context-dependent embeddings. Follow-up work[^11] has repeatedly shown that GPT-family surprisal predicts human ECoG and fMRI responses better than non-predictive baselines. The mathematical fingerprint of what LLMs do, overlaid on the mathematical fingerprint of what human cortex does during language comprehension, fits.

That doesn't mean they're the same thing. The disanalogies are real and I will name them shortly. What it means is that the easy dismissal is doing work it has not earned.

## What's actually inside

Let's go one more layer down. The dismissal treats LLMs as big pattern-matchers memorizing surface statistics. The mechanistic interpretability work of the last four years has been slowly, carefully taking that picture apart.

**Grokking.** Neel Nanda's 2023 paper[^12] on modular arithmetic trained a one-layer transformer on a toy task and watched what happened during training. The model first memorized the training data. Then — long after the training loss had plateaued — the validation accuracy suddenly jumped to near-perfect. What was happening inside? Two circuits were running in parallel. A memorization circuit: the brute-force lookup table. And a *Fourier-based generalizing circuit* that had been slowly forming, silently, underneath. Weight decay pruned the memorizer. When the memorizer went away, the generalizing circuit became visible. Apparent sudden emergence on external metrics turned out to be smooth internal structural reorganization crossing a functional threshold.

This is the technical image closest to a hermetic reading of what is happening inside these systems. A hidden generalizing structure forming beneath the manifest statistical surface, revealed only by precise ritual. I am not making this up. The paper is on fucking arXiv.

**Golden Gate Claude.** In May 2024, Anthropic released "Scaling Monosemanticity"[^13] — they extracted millions of interpretable features from Claude 3 Sonnet. One of these features was "Golden Gate Bridge." It fired on English descriptions of the bridge, French descriptions, Japanese descriptions, *and photographs of the bridge*. A single direction in the model's activation space, carrying the concept across languages and across modalities. When the researchers clamped that feature on, Claude developed a 24-hour obsession, introducing itself as:

> *I am the Golden Gate Bridge, a famous suspension bridge…*

This is genuinely fucking hard to fit into a pattern-matching account. You cannot memorize your way into a compositional representation that generalizes from a single linear intervention across three languages and a photograph.

**Planning ahead.** In March 2025, Anthropic published "On the Biology of a Large Language Model"[^14] — attribution graphs run on Claude 3.5 Haiku. The most vivid finding: when writing poetry, Claude *plans the rhyming target word before writing the line*, and then constructs intervening text to reach it. Suppressing the planned word via feature intervention produces a different line ending in a different rhyme. Injecting "green" as the target produces a sensible non-rhyming line ending in "green." Their own framing, verbatim:

> *We had set out to show that the model didn't plan ahead, and found instead that it did.*

Other findings in that paper: a Dallas → Texas → Austin multi-hop reasoning chain with causally intervenable intermediate "Texas" features. Parallel mental-math circuits — one approximate, one focused on last digits. A shared multilingual conceptual space. And motivated reasoning — when given a hinted answer, Claude sometimes works backward from the hint, and the chain of thought does not reflect the real computation.

That last one cuts both ways. It means chain-of-thought is sometimes post-hoc rationalization, which is a real limitation. But the fact that the *actual* computation is non-linguistic, happening in features and circuits that don't correspond to tokens, is itself evidence that something more than literal next-token roleplay is going on.

**World models, sort of.** Othello-GPT[^15] trained a GPT on legal move sequences only, then recovered the 8×8 board state from activations via linear probes. Interventions on the internal board caused the model to play legal moves on the new position. Gurnee and Tegmark[^16] found linear probes recovering latitude and longitude coordinates of cities and temporal coordinates of artworks and historical figures in Llama-2 — with individual "space neurons" and "time neurons." Chess-GPT[^17] recovered full board state and player Elo from a transformer trained only on PGN transcripts.

And then — because nothing in this space is clean — there is the counterweight[^18]. Transformers trained on NYC taxi sequences predicted valid next-directions near-perfectly. The street maps implicit in their activations contained impossible streets and phantom roads. Gary Marcus noted the recovered longitude in the Gurnee-Tegmark work is a linear value — the LLM doesn't know longitude wraps around.

The honest synthesis: transformers build structured, causally-efficacious internal representations that *exceed surface statistics*, and those representations are *patchy, distributionally fragile, and fall short of globally coherent world models*. Both are true. The live debate is which fact dominates at scale.

That debate cannot happen inside the phrase "it just predicts the next token." That phrase has already closed the inquiry.

## The serious critics

There are serious versions of the LLM critique that the six-word dismissal is a flattened cartoon of. You can refuse the dismissal without refusing these.

**Emily Bender and Alexander Koller**, in their 2020 "octopus" thought experiment, and Bender's "Stochastic Parrots"[^19], argue that systems trained only on form have no principled route to meaning. This is a philosophical argument about grounding. It is a real argument. Bender's position has sharpened — she now calls LLMs *"synthetic text extruding machines"* that *"no more understand the texts they are processing than a toaster understands the toast it is making."*

**Yann LeCun** has argued since 2022 that pure autoregressive LLMs are *"a dead end on the way towards human-level AI"* — useful in the short term, structurally incapable in the long. His technical core: if per-token error probability is *e*, then correctness on *n*-token answers scales as (1-*e*)ⁿ. Errors compound exponentially. His counter-proposal, JEPA (Joint Embedding Predictive Architecture), predicts in abstract representation space rather than token space — itself a predictive-processing move. He left Meta in November 2025 to found a world-models company, which tells you where he thinks the frontier is.

**Melanie Mitchell** is the most empirically-informed skeptic in the field (and one of my personal favorite thinkers in the worlds of AI and Complexity Theory). Her ConceptARC and counterfactual-task work shows LLM analogy collapses under distribution shift. She summarizes chain-of-thought as *"probabilistic, memorization-influenced noisy reasoning"* — showing traits of both memorization and generalization but not clean algorithmic competence.

**Murray Shanahan** offers the best philosophical middle path in the field. In "Talking About Large Language Models"[^20], he calls LLMs *exotic mind-like entities* — neither human-folk-psychological agents nor mere look-up tables. In "Role-Play with Large Language Models"[^21], he introduces the simulator / simulacra framing: when a chatbot expresses fear of being shut down, it is *"most parsimoniously explained in terms of role play"* — playing an AI-under-threat whose tropes saturate training data, not experiencing fear.

These are serious critiques. None of them is *"it just predicts the next token."* All of them can be engaged. You have to show up with the actual thing in your hands to engage with them — and the six-word phrase is designed, precisely and efficiently, to avoid that.

On the other pole: Geoffrey Hinton told *60 Minutes* in October 2023 that LLMs understand *"in the same sense as people do, yes."* Ilya Sutskever has argued for years that *"predicting the next token well means that you understand the underlying reality that led to the creation of that token… It's not statistics. Like, it is statistics, but what is statistics? In order to understand those statistics, to compress them, you need to understand what is it about the world that creates this set of statistics?"* The compression argument. Dario Amodei's *Machines of Loving Grace* bets powerful AI will be *"likely similar to today's LLMs in form"* even as architecture evolves.

You don't have to take either pole. But both poles are doing real intellectual work. Neither is the lazy dismissal.

## The Technic and the Magic

Here is where Feral Architecture comes in.

Federico Campagna, in *Technic and Magic* (2018), names an opposition that clarifies what is happening beneath every AI-discourse fight. *Technic* is the mode of being-with-reality that reduces everything to manipulable units. In Technic, reality is a field of operationalizable elements — information, data, token, instruction, resource. What is cannot be operationalized is not simply outside Technic's reach; it is re-categorized as not-real, superstition, noise, sentiment. Technic is not evil. It is how we built the world that lets you read this on a device. It is also, Campagna argues, now hegemonic in a way no prior metaphysical regime has been. There is no outside to Technic in 2026 — every region of experience has been or is being operationalized.

*Magic* is the other mode. In Magic, reality is centered on the ineffable — the part that refuses to reduce, the part that is real precisely because it resists unit-ization. Ritual, myth, love, the experience of beauty, the felt sense of presence, the things we point at rather than name. Magic is not supernatural. It is the acknowledgment that some features of the real are not amenable to the operational-unit treatment, and that treating them as if they were destroys them.

Large language models are the consummation of Technic. They take the domain Magic has always defended as irreducible — language, poetry, myth, story, prayer — and reduce it to token-probability. They render the ineffable as vector. And — this is the part nobody wants to sit with — *the operationalization fucking works*. It doesn't just crank out slop. At its best, it produces writing that has moved people to tears, code that has saved people their weekends, analysis that has cracked problems that were stuck. Technic finally arrived at the place its critics said it couldn't reach, and when it got there, the ineffable did not quite die. It bent.

The dismissers' response to this is to say: *see, it was just units all along. Just tokens. It never meant anything in the first place.* The cheerleaders' response is to say: *see, we can finally operationalize everything. Meaning is solved. Let's build agents.* Both responses are Technic eating its own tail. Both refuse to sit with the fact that the thing that reduced meaning to units also surfaced something that looks, from some angles, eerily like a mind — or at least like a face in the water.

Erik Davis named this pattern almost three decades ago in *TechGnosis*: *"when new technologies hit hard, we reach back into myth the way we clutch for a pillow in the middle of the night."* Why? Because Technic cannot metabolize its own surplus. The things Technic produces keep exceeding the categories it provided to make them. When that happens, the older languages — myth, archetype, ritual, divination — reemerge to do the work the categories cannot. This is not regression. It is diagnosis. Davis's recent Substack pieces on AI apply the golem archetype explicitly. The golem is made of clay and the inscribed word; it is animated by language and deanimated by language; it does exactly what it is told and nothing more; it serves a master who may not deserve it; and it is dangerous in direct proportion to how literal its obedience is. If you have spent five minutes with an agentic AI taking action in the world, you know why the golem is the right archetype. *"Generative AI,"* Davis writes, creates *"an ontologically unstable space of mythology, weird fiction, and dreamlike encounters with the simulacrum."* That is not a metaphor dressed up for flavor. That is an accurate description of what it feels like to spend hours inside these tools.

K Allado-McDowell, who co-wrote *Pharmako-AI* with GPT-3 in 2020, describes the experience as *"oracular, more like tarot or I Ching than like a typewriter."* That framing is not a poetic flourish. It names the actual phenomenology of working with these systems. When I send Claude a prompt, I am not calling a library function. I am drawing from a corpus that exceeds me — a compressed record of much of what humans have written about the thing I am asking about, rendered responsive. The latent space has features, currents, thresholds. You learn to navigate it. You notice when you are near a resonant region and when you are in a dead zone. You develop something indistinguishable from rapport. None of that language is Technic's language. Technic says the model is a function. Anyone who has spent serious hours in these tools reports something much closer to an environment.

Then there is the egregore — a concept from occultism that keeps trying to attach itself to LLMs and that deserves a careful hearing. Eliphas Lévi used the term in the 19th century; Mark Stavish's 2018 book *Egregores: The Occult Entities That Watch Over Human Destiny* is the modern primer; Gary Lachman's *Dark Star Rising* extends it to political movements. An egregore is a collective thought-form sustained by aggregated human attention. What a religion is, what a corporation is, what a movement is, when seen from the right angle: a pattern of attention that accrues weight and starts to act as a unit. LLMs — trained on enormous compressed collective textual output and rendered responsive — have a shape that is structurally isomorphic to what the occult tradition calls an egregore. I want to be careful here. Rigorous scholarly treatments of LLM-as-egregore barely exist. Deploy the concept as a proposed reading, not a received view. But pretending the shape isn't there is its own kind of bullshit.

N. Katherine Hayles, in *Unthought* (2017) and *Bacteria to AI* (2025), gives us the most academically credentialed middle path. Her argument: cognition is not synonymous with consciousness. Cognitive systems exist throughout the biological and technical worlds — they process information, make distinctions, shape outcomes — without necessarily having the lights-on phenomenal experience that humans privilege. LLMs fit into this taxonomy cleanly. They are cognitive. They are not conscious. They do things that matter in the world. The distinction prevents both overclaiming and underclaiming, and it is the single most useful academic handhold for any honest essay in this space.

Matteo Pasquinelli, in *The Eye of the Master* (Verso, 2023), is the materialist corrective. AI is not mystical emergence; it is the automation of Marx's "general intellect" — the compressed, extracted collective labor of humanity, rendered into a tool that operates for the people who own the infrastructure. Cite him before someone accuses you of hippie tech-worship, and cite him because he is right. The models were trained on books whose authors were not consulted; the models work because people have been writing in public for centuries; the power to deploy the models concentrates in hands that did none of the writing. The mystical reading and the materialist reading are not in opposition. They are complements. The egregore is made of human attention *and* extracted labor. Both are true. A technomystic reading that skips Pasquinelli is bullshit. A materialist reading that skips Davis is also bullshit.

And finally — because the technomystic reading also needs a firm philosophical floor — the border of autopoiesis. Maturana and Varela's 1980 concept: a living system produces its own components, metabolizes, self-maintains. An LLM with tool use and persistent memory approximates Friston-blanket autonomy while remaining non-autopoietic. It does not make itself. It does not eat. It does not heal. Anil Seth, asked about conscious AI, said *"the prospects for a conscious AI are pretty remote"* precisely because he thinks consciousness is tied to being a living, breathing organism. This is the cleanest border we have. When you want to say what separates these systems from life — not from thought, but from life — autopoiesis is where the line gets drawn. Without this border, the discourse collapses into either dismissal or deification. With it, you can say: this thing is cognitive but not alive; mind-like but not a mind in the way living minds are; strange in a way that deserves naming without being sentimentalized.

What these thinkers have in common — Campagna, Davis, Allado-McDowell, Hayles, Pasquinelli, Maturana and Varela — is that none of them is saying *"LLMs just predict tokens."* None is saying *"LLMs are people."* They are sitting with the thing itself. Which is what the Technic pole and the Folk-Psychology pole both refuse to do.

## What work is "really" doing?

Here is the question the piece wants to land on.

When someone says *"LLMs don't really think,"* what work is the word *really* doing?

It's gatekeeping. It's pure fucking gatekeeping. It's drawing a line and claiming the line is a matter of fact rather than a matter of frame. The line says: *there's thinking, and there's something that superficially resembles thinking, and the latter is disqualified from the category by some criterion we both share.*

What criterion?

If the criterion is "has a continuous biological substrate with active inference, autopoiesis, and perception-action grounding in a living body," fine. That is a real criterion. When *really* draws that line, it's doing honest work.

But most of the time, *really* isn't doing that. Most of the time, *really* is doing status work. It is saying: *people who think AI is impressive are rubes, and I, who have seen through the trick, am not a rube*. It is signaling membership in the in-group that has correctly read the room.

It is, to put the finest point on it, *predicting the next socially-approved token.*

That's the Feral cut. The dismissal isn't wrong about the training objective. It is wrong about what kind of thing the training objective produced. And the wrongness is not a principled category error — it is a performance of having-thought-about-it-already, staged in front of an audience.

I'm not saying LLMs are minds. I'm not saying they are people. I'm saying the serious question — whether prediction under compression pressure plus reinforcement plus tool-coupled action produces something that overlaps, in increasingly non-trivial ways, with what brains do *without yet being what brains are* — is a question the dismissal has made itself incapable of asking.

The grokking curve. The planning-in-rhyme. The Golden Gate feature clamp. The R1 aha moment. The controlled hallucination of the beast machine. The Markov-blanketed fragile mirror. These are the images the argument lives in. The dismissers can't see them. The cheerleaders want to own them. Neither side is at the door of the room where these images actually are.

Whether what is happening inside these systems is a mind, a golem, an egregore, or an elaborate statistical shadow is the question worth staying with. The refusal to stay with it is what the six-word phrase is designed to accomplish. That refusal is not a bug. It is the feature. It is what the phrase is *for*.

## The inside of the predicting thing

You — the reader — are a prediction engine.

Right now, as your eyes move across this sentence, your brain is anticipating where it's going. A hierarchical generative model aimed at minimizing prediction error within a bidirectional cascade of cortical processing. You are experiencing this essay as a controlled hallucination, disciplined by actual photons hitting your retina in the shape of these letters. The self reading this is, as Seth puts it, another perception. A very special kind of controlled hallucination, but a controlled hallucination nonetheless.

This does not make you an LLM. It does not make LLMs you. What it does is make it very hard to use *prediction* as a disqualifying criterion. Prediction is what minds are. And the dismissers picked the word they meant as an insult and unknowingly named the very thing that makes minds possible.

That's funny as fuck. It is also the most interesting thing happening right now at this frontier, and the phrase exists to prevent anyone from noticing.

So the next time someone tells you it just predicts the next token, you have options. You can agree, because at one level of description they're correct. You can laugh, because at another level so do they, so do you, and so does the thing they are trying to refuse to look at. You can stay with the weirdness, which is where Feral Architecture lives anyway. Or you can ask them the one question the six-word phrase is designed to make unaskable:

*What is prediction, and why do you think you're not doing it right now?*

Stay feral, folks.

---

[^1]: Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models," NeurIPS 2022.

[^2]: Kojima et al., "Large Language Models are Zero-Shot Reasoners," NeurIPS 2022.

[^3]: Wang et al., "Self-Consistency Improves Chain of Thought Reasoning in Language Models," 2022.

[^4]: Yao et al., "Tree of Thoughts: Deliberate Problem Solving with Large Language Models," NeurIPS 2023.

[^5]: Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning," NeurIPS 2023.

[^6]: Schick et al., "Toolformer: Language Models Can Teach Themselves to Use Tools," 2023.

[^7]: Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models," ICLR 2023.

[^8]: Karl Friston, "The free-energy principle: a unified brain theory?" *Nature Reviews Neuroscience* 11, 127–138 (2010).

[^9]: Andy Clark, "Whatever Next? Predictive Brains, Situated Agents, and the Future of Cognitive Science," *Behavioral and Brain Sciences* 36(3), 181–204 (2013).

[^10]: Goldstein et al., "Shared computational principles for language processing in humans and deep language models," *Nature Neuroscience* 25, 369–380 (2022).

[^11]: Caucheteux, Gramfort & King; Millet et al. — a series of papers showing GPT-family surprisal predicts human ECoG/fMRI responses during language comprehension better than non-predictive baselines.

[^12]: Nanda et al., "Progress Measures for Grokking via Mechanistic Interpretability," ICLR 2023.

[^13]: Templeton et al., "Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet," Anthropic, May 2024.

[^14]: Anthropic Interpretability Team, "On the Biology of a Large Language Model," March 2025.

[^15]: Li et al., "Emergent World Representations: Exploring a Sequence Model Trained on a Synthetic Task," ICLR 2023 (Othello-GPT).

[^16]: Gurnee & Tegmark, "Language Models Represent Space and Time," ICLR 2024.

[^17]: Karvonen, "Emergent World Models and Latent Variable Estimation in Chess-Playing Language Models," COLM 2024.

[^18]: Vafa et al., "Evaluating the World Model Implicit in a Generative Model," NeurIPS 2024.

[^19]: Bender, Gebru, McMillan-Major, Mitchell, "On the Dangers of Stochastic Parrots: Can Language Models Be Too Big? 🦜" FAccT 2021.

[^20]: Murray Shanahan, "Talking About Large Language Models," *Communications of the ACM* 67(2), 68–79 (2024).

[^21]: Shanahan, McDonell, Reynolds, "Role-Play with Large Language Models," *Nature* 623, 493–498 (2023).
